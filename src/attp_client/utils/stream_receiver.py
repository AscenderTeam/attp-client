import msgpack

from typing import AsyncIterable, AsyncIterator, Callable, Generic, TypeVar
from attp_core.rs_api import PyAttpMessage


T = TypeVar("T")


class StreamReceiver(Generic[T]):
    def __init__(
        self,
        _generator: AsyncIterable[PyAttpMessage],
        *,
        formatter: Callable[[PyAttpMessage], T | None] | None = None,
    ) -> None:
        self.generator = _generator
        self.formatter = formatter

    def __aiter__(self) -> AsyncIterator[T]:
        return self.__iter_stream()

    def default_formatter(self, data: PyAttpMessage):
        if not data.payload:
            return None
        
        return msgpack.unpackb(data.payload)

    async def __iter_stream(self):
        async for frame in self.generator:
            if not self.formatter:
                formatted = self.default_formatter(frame)
                if formatted is not None:
                    yield formatted
                continue

            formatted = self.formatter(frame)
            if formatted is not None:
                yield formatted
