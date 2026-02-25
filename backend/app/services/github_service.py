from __future__ import annotations

import asyncio
import base64
import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx

from app.core.config import settings
from app.services.file_utils import FileItem, load_gitignore_patterns, is_relevant_file


@dataclass
class RepoRef:
    owner: str
    repo: str


def parse_repo_url(repo_url: str) -> RepoRef:
    repo_url = repo_url.rstrip("/")
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    parts = repo_url.split("/")
    if len(parts) < 2:
        raise ValueError("Invalid repo URL")
    owner = parts[-2]
    repo = parts[-1]
    return RepoRef(owner=owner, repo=repo)


class GitHubService:
    def __init__(self) -> None:
        self.base_url = settings.github_api_base

    def _headers(self, token: str | None) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "acra-ai",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def fetch_repo_files_via_api(
        self, repo_url: str, token: str | None, pr_number: int | None
    ) -> list[FileItem]:
        ref = parse_repo_url(repo_url)
        async with httpx.AsyncClient(timeout=settings.request_timeout_s) as client:
            if pr_number:
                files = await self._fetch_pr_files(client, ref, token, pr_number)
            else:
                files = await self._fetch_repo_tree_files(client, ref, token)

            gitignore_lines = await self._fetch_gitignore(client, ref, token)
            spec = load_gitignore_patterns(gitignore_lines)

            results: list[FileItem] = []
            for path in files:
                if spec.match_file(path):
                    continue
                if not is_relevant_file(path):
                    continue
                content = await self._fetch_file_content(client, ref, token, path)
                if content is None:
                    continue
                results.append(FileItem(path=path, content=content))
            return results

    async def _fetch_repo_tree_files(
        self, client: httpx.AsyncClient, ref: RepoRef, token: str | None
    ) -> list[str]:
        branch = await self._fetch_default_branch(client, ref, token)
        tree_ref = branch or "HEAD"
        url = f"{self.base_url}/repos/{ref.owner}/{ref.repo}/git/trees/{tree_ref}?recursive=1"
        resp = await client.get(url, headers=self._headers(token))
        self._check_rate_limit(resp)
        resp.raise_for_status()
        data = resp.json()
        return [item["path"] for item in data.get("tree", []) if item.get("type") == "blob"]

    async def _fetch_default_branch(
        self, client: httpx.AsyncClient, ref: RepoRef, token: str | None
    ) -> str | None:
        url = f"{self.base_url}/repos/{ref.owner}/{ref.repo}"
        resp = await client.get(url, headers=self._headers(token))
        self._check_rate_limit(resp)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        return data.get("default_branch")

    async def _fetch_pr_files(
        self, client: httpx.AsyncClient, ref: RepoRef, token: str | None, pr_number: int
    ) -> list[str]:
        url = f"{self.base_url}/repos/{ref.owner}/{ref.repo}/pulls/{pr_number}/files"
        files: list[str] = []
        page = 1
        while True:
            resp = await client.get(
                url,
                headers=self._headers(token),
                params={"page": page, "per_page": 100},
            )
            self._check_rate_limit(resp)
            resp.raise_for_status()
            items = resp.json()
            if not items:
                break
            files.extend(item["filename"] for item in items)
            page += 1
        return files

    async def _fetch_gitignore(
        self, client: httpx.AsyncClient, ref: RepoRef, token: str | None
    ) -> list[str]:
        url = f"{self.base_url}/repos/{ref.owner}/{ref.repo}/contents/.gitignore"
        resp = await client.get(url, headers=self._headers(token))
        self._check_rate_limit(resp)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        content = data.get("content")
        if not content:
            return []
        decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
        return decoded.splitlines()

    async def _fetch_file_content(
        self, client: httpx.AsyncClient, ref: RepoRef, token: str | None, path: str
    ) -> str | None:
        url = f"{self.base_url}/repos/{ref.owner}/{ref.repo}/contents/{path}"
        resp = await client.get(url, headers=self._headers(token))
        self._check_rate_limit(resp)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        if data.get("encoding") == "base64" and data.get("content"):
            return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        return None

    async def fetch_repo_files_via_git(
        self, repo_url: str, token: str | None
    ) -> list[FileItem]:
        with TemporaryDirectory() as tmpdir:
            await self._git_clone(repo_url, tmpdir, token)

            gitignore_path = Path(tmpdir) / ".gitignore"
            gitignore_lines = gitignore_path.read_text(encoding="utf-8", errors="ignore").splitlines() if gitignore_path.exists() else []
            spec = load_gitignore_patterns(gitignore_lines)

            results: list[FileItem] = []
            for root, _, files in os.walk(tmpdir):
                for filename in files:
                    rel_path = os.path.relpath(os.path.join(root, filename), tmpdir)
                    if spec.match_file(rel_path):
                        continue
                    if not is_relevant_file(rel_path):
                        continue
                    file_path = Path(tmpdir) / rel_path
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                    except OSError:
                        continue
                    results.append(FileItem(path=rel_path, content=content))
            return results

    async def _git_clone(self, repo_url: str, dest: str, token: str | None) -> None:
        args = ["git", "clone", "--depth", "1"]
        if token:
            auth = base64.b64encode(f"x-access-token:{token}".encode("utf-8")).decode("utf-8")
            args.extend(["-c", f"http.extraHeader=Authorization: Basic {auth}"])
        args.extend([repo_url, dest])
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"git clone failed: {stderr.decode('utf-8', errors='ignore')}")

    def _check_rate_limit(self, resp: httpx.Response) -> None:
        if resp.status_code == 403:
            remaining = resp.headers.get("X-RateLimit-Remaining")
            if remaining == "0":
                raise RuntimeError("GitHub API rate limit exceeded")
