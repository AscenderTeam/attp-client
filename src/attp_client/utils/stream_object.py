from inspect import isasyncgenfunction, isfunction
from typing import AsyncGenerator, AsyncIterable, AsyncIterator, Iterable, Iterator, TypeAlias

from attp_client.misc.fixed_basemodel import FixedBaseModel

from collections.abc import AsyncIterable as AsyncIterableABC, AsyncIterator as AsyncIteratorABC


IterateWrapper: TypeAlias = (Iterable[FixedBaseModel] | Iterator[FixedBaseModel] | 
                             AsyncGenerator[FixedBaseModel, None] | AsyncIterable[FixedBaseModel] |
                            AsyncIterator[FixedBaseModel]
                            )

class StreamObject:    
    def __init__(
        self, 
        _iterable: IterateWrapper | None = None
    ) -> None:
        self._iterable = _iterable
        self.is_async = False
        
        if isinstance(_iterable, (AsyncIterableABC, AsyncIteratorABC)):
            self.is_async = True
    
    def iterate(self) -> IterateWrapper | None:
        return self._iterable