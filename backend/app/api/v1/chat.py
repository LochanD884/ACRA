from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.analysis import Analysis
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.openrouter_service import OpenRouterService
from app.core.config import settings

router = APIRouter()
openrouter = OpenRouterService()

SYSTEM_PROMPT = """You are an assistant that answers questions about a codebase review. Use the summary and issues provided. Be concise and actionable. When proposing improvements, include concrete code-level fixes with short snippets."""


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    if not settings.openrouter_api_key:
        raise HTTPException(status_code=400, detail="OpenRouter is not configured")
    if not payload.analysis_id and not payload.repo_url:
        raise HTTPException(status_code=400, detail="analysis_id or repo_url is required")

    summary = ""
    issues_block = ""
    if payload.analysis_id:
        result = await db.execute(
            select(Analysis).options(selectinload(Analysis.issues)).where(Analysis.id == payload.analysis_id)
        )
        analysis = result.scalar_one_or_none()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        summary = analysis.summary or ""
        if analysis.issues:
            top = analysis.issues[:10]
            lines = []
            for issue in top:
                loc = (
                    f" (lines {issue.line_start}-{issue.line_end})"
                    if issue.line_start and issue.line_end
                    else f" (line {issue.line_start})"
                    if issue.line_start
                    else ""
                )
                lines.append(f"- [{issue.severity}] {issue.category} {issue.file_path}{loc}: {issue.message}")
            issues_block = "\n".join(lines)

    user_prompt = f"Summary:\n{summary}\n\nTop issues:\n{issues_block or 'No issues listed.'}\n\nQuestion: {payload.question}"
    answer = await openrouter.chat(SYSTEM_PROMPT, user_prompt)
    return ChatResponse(answer=answer)
