import asyncio
import httpx

from app.core.config import settings


class OpenRouterService:
    def __init__(self) -> None:
        self.base_url = settings.openrouter_api_base
        self.model = settings.openrouter_model

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }

    async def analyze_chunk(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        attempts = 3
        backoff = 1.5
        last_exc: Exception | None = None
        async with httpx.AsyncClient(timeout=settings.request_timeout_s) as client:
            for attempt in range(1, attempts + 1):
                try:
                    resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self._headers(),
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                except httpx.HTTPStatusError as exc:
                    status = exc.response.status_code
                    if status in {408, 429, 500, 502, 503, 504} and attempt < attempts:
                        await asyncio.sleep(backoff ** attempt)
                        last_exc = exc
                        continue
                    raise
                except httpx.RequestError as exc:
                    if attempt < attempts:
                        await asyncio.sleep(backoff ** attempt)
                        last_exc = exc
                        continue
                    raise
        if last_exc:
            raise last_exc
        raise RuntimeError("OpenRouter request failed")

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        return await self.analyze_chunk(system_prompt, user_prompt)
