import asyncio
from typing import Any, AsyncIterator, Callable, Generic, TypeVar

import msgpack
from reactivex import Observable
from attp_core.rs_api import PyAttpMessage


T = TypeVar("T")


class StreamReceiver(Generic[T]):
    def __init__(
        self,
        observable: Observable[PyAttpMessage],
        *,
        formatter: Callable[[PyAttpMessage], T | None] | None = None,
    ) -> None:
        self.observable = observable
        self.formatter = formatter or self.__default_formatter
        self.queue: asyncio.Queue[PyAttpMessage] = asyncio.Queue()
        self.completed = asyncio.Event()
        self.subscription = None
        self.error: Exception | None = None
        self.started = False

    def __aiter__(self) -> AsyncIterator[T]:
        return self.__iter_stream()

    def __subscribe(self) -> None:
        if self.started:
            return
        self.started = True
        self.subscription = self.observable.subscribe(
            on_next=self.queue.put_nowait,
            on_error=self.__on_error,
            on_completed=self.completed.set,
        )

    async def __iter_stream(self) -> AsyncIterator[T]:
        self.__subscribe()

        try:
            while True:
                if self.error:
                    raise self.error

                if self.completed.is_set() and self.queue.empty():
                    break

                message = await self.queue.get()
                formatted = self.formatter(message)
                if formatted is None:
                    continue
                yield formatted
        finally:
            self.__dispose()

    def __on_error(self, exc: Exception):
        self.error = exc
        self.completed.set()

    def __dispose(self):
        if self.subscription:
            self.subscription.dispose()
            self.subscription = None

    def __default_formatter(self, msg: PyAttpMessage) -> Any | None:
        if msg.payload is None:
            return None
        return msgpack.unpackb(msg.payload)
