import asyncio
from typing import Generic, TypeVar


T = TypeVar("T")


class AttpReceiver(Generic[T]):
    def __init__(self) -> None:
        self._queue: asyncio.Queue[T] = asyncio.Queue()

    def on_next(self, item: T) -> None:
        self._queue.put_nowait(item)

    async def get(self) -> T:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()
