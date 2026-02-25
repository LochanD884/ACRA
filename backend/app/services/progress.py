import asyncio
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProgressUpdate:
    analysis_id: int
    status: str
    progress: int
    message: str | None = None
    payload: dict[str, Any] | None = None


class ProgressHub:
    def __init__(self) -> None:
        self._queues: dict[int, asyncio.Queue[ProgressUpdate]] = {}

    def get_queue(self, analysis_id: int) -> asyncio.Queue[ProgressUpdate]:
        if analysis_id not in self._queues:
            self._queues[analysis_id] = asyncio.Queue()
        return self._queues[analysis_id]

    async def publish(self, update: ProgressUpdate) -> None:
        queue = self.get_queue(update.analysis_id)
        await queue.put(update)


progress_hub = ProgressHub()
