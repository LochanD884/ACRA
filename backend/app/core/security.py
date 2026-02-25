from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from fastapi import Header, HTTPException, Request

from app.core.config import settings

SENSITIVE_FIELDS = {"token", "authorization", "api_key", "openrouter_api_key", "github_token"}


def redact(value: str | None) -> str | None:
    if value is None:
        return None
    if len(value) <= 6:
        return "***"
    return value[:2] + "***" + value[-2:]


def require_api_key(
    request: Request,
    authorization: str | None = Header(default=None),
    x_acra_api_key: str | None = Header(default=None),
):
    if request.method == "OPTIONS":
        return
    if not settings.api_key:
        return
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if not token:
        token = x_acra_api_key
    if not token:
        token = request.query_params.get("api_key")
    if token != settings.api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")


@dataclass
class RateLimitEntry:
    window_start: float
    count: int


class RateLimiter:
    def __init__(self, limit: int, window_s: int) -> None:
        self.limit = max(1, limit)
        self.window_s = max(1, window_s)
        self._entries: dict[str, RateLimitEntry] = {}

    def _key(self, request: Request) -> str:
        client = request.client.host if request.client else "unknown"
        return f"{client}:{request.url.path}"

    def allow(self, request: Request) -> bool:
        now = time.monotonic()
        key = self._key(request)
        entry = self._entries.get(key)
        if not entry or now - entry.window_start >= self.window_s:
            self._entries[key] = RateLimitEntry(window_start=now, count=1)
            return True
        if entry.count >= self.limit:
            return False
        entry.count += 1
        return True


def rate_limit_middleware(limiter: RateLimiter) -> Callable:
    async def _middleware(request: Request, call_next):
        if request.url.path.startswith("/api/"):
            if not limiter.allow(request):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
        return await call_next(request)

    return _middleware


def security_headers_middleware() -> Callable:
    async def _middleware(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

    return _middleware
