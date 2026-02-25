from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.analysis import Analysis
from app.models.issue import Issue
from app.services.file_utils import chunk_text
from app.services.github_service import GitHubService
from app.services.openrouter_service import OpenRouterService
from app.services.progress import ProgressUpdate, progress_hub

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a senior code reviewer. Analyze the provided code for security issues (OWASP Top 10), performance optimizations, and general code quality.\nReturn strict JSON with fields: summary (string), quality_score (0-100), issues (array). Each issue has: file_path, line_start (int or null), line_end (int or null), severity (low|medium|high|critical), category (security|performance|quality), message, recommendation.\nRecommendation must include a concrete code-level fix, ideally with a short before/after snippet.\nDo not include any text outside JSON."""


@dataclass
class AnalysisInput:
    repo_url: str
    pr_number: int | None
    github_token: str | None
    allow_git_clone: bool


class AnalysisAgent:
    def __init__(self) -> None:
        self.github = GitHubService()
        self.openrouter = OpenRouterService()

    async def run(self, analysis_id: int, session: AsyncSession, payload: AnalysisInput) -> None:
        try:
            await self._update_status(session, analysis_id, "fetching", 5, "Fetching repository")
            files = await self._fetch_files(payload)

            await self._update_status(session, analysis_id, "chunking", 15, f"Preparing {len(files)} files")
            chunks = self._build_chunks(files)

            await self._update_status(session, analysis_id, "analyzing", 30, f"Analyzing {len(chunks)} chunks")
            issues: list[Issue] = []
            summaries: list[str] = []
            scores: list[int] = []

            semaphore = asyncio.Semaphore(max(1, settings.max_concurrent_chunks))

            async def analyze_one(idx: int, chunk: str) -> ParsedResult | None:
                async with semaphore:
                    user_prompt = chunk
                    response = await self.openrouter.analyze_chunk(SYSTEM_PROMPT, user_prompt)
                    parsed = self._parse_response(response)
                    return parsed

            tasks = [asyncio.create_task(analyze_one(i, c)) for i, c in enumerate(chunks, start=1)]
            completed = 0
            total = max(1, len(tasks))

            for task in asyncio.as_completed(tasks):
                parsed = await task
                completed += 1
                progress = 30 + int(60 * completed / total)
                await self._update_status(
                    session,
                    analysis_id,
                    "analyzing",
                    progress,
                    f"Chunk {completed}/{total}",
                )

                if parsed is None:
                    continue

                summaries.append(parsed.summary)
                scores.append(parsed.quality_score)
                for item in parsed.issues:
                    issues.append(
                        Issue(
                            analysis_id=analysis_id,
                            file_path=item.get("file_path", "unknown"),
                            line_start=item.get("line_start"),
                            line_end=item.get("line_end"),
                            severity=item.get("severity", "low"),
                            category=item.get("category", "quality"),
                            message=item.get("message", ""),
                            recommendation=item.get("recommendation"),
                        )
                    )

            await self._update_status(session, analysis_id, "persisting", 92, "Saving results")
            analysis = await session.get(Analysis, analysis_id)
            if analysis:
                analysis.summary = "\n".join([s for s in summaries if s])[:4000] if summaries else ""
                if scores:
                    analysis.quality_score = int(sum(scores) / len(scores))
                analysis.status = "completed"
                analysis.progress = 100
                session.add_all(issues)
                await session.commit()

            await progress_hub.publish(ProgressUpdate(analysis_id=analysis_id, status="completed", progress=100))
        except Exception as exc:
            logger.exception("Analysis failed: %s", exc)
            analysis = await session.get(Analysis, analysis_id)
            if analysis:
                analysis.status = "failed"
                analysis.progress = 100
                await session.commit()
            await progress_hub.publish(
                ProgressUpdate(analysis_id=analysis_id, status="failed", progress=100, message=str(exc))
            )

    async def _fetch_files(self, payload: AnalysisInput):
        if payload.allow_git_clone:
            try:
                return await self.github.fetch_repo_files_via_git(payload.repo_url, payload.github_token)
            except Exception as exc:
                logger.warning("git clone failed, falling back to GitHub API: %s", exc)
        return await self.github.fetch_repo_files_via_api(payload.repo_url, payload.github_token, payload.pr_number)

    def _build_chunks(self, files):
        chunks: list[str] = []
        for file in files[: settings.max_files]:
            if len(file.content.encode("utf-8", errors="ignore")) > settings.max_file_bytes:
                continue
            parts = chunk_text(file.content, settings.chunk_char_limit)
            for idx, part in enumerate(parts, start=1):
                header = f"\n\n# File: {file.path} (part {idx}/{len(parts)})\n"
                chunks.append(header + part)
        return chunks

    def _parse_response(self, response: str):
        text = response.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return None
            try:
                data = json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return None

        if not isinstance(data, dict):
            return None

        summary = data.get("summary", "")
        quality_score = int(data.get("quality_score", 0))
        issues = data.get("issues", []) if isinstance(data.get("issues"), list) else []
        return ParsedResult(summary=summary, quality_score=quality_score, issues=issues)

    async def _update_status(self, session: AsyncSession, analysis_id: int, status: str, progress: int, message: str):
        analysis = await session.get(Analysis, analysis_id)
        if analysis:
            analysis.status = status
            analysis.progress = progress
            await session.commit()
        await progress_hub.publish(
            ProgressUpdate(analysis_id=analysis_id, status=status, progress=progress, message=message)
        )


@dataclass
class ParsedResult:
    summary: str
    quality_score: int
    issues: list[dict]
