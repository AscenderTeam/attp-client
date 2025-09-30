import asyncio
from typing import Generic, TypeVar
from reactivex import Observable


T = TypeVar("T")


class ContextAwaiter(Generic[T]):
    def __init__(
        self, 
        observable: Observable[T],
    ) -> None:
        self.observable = observable
        self.response = asyncio.Future[T]()
        self.event = asyncio.Event()
        
    async def wait(self) -> T:
        self.observable.subscribe(
            on_next=self.__define_response,
            on_error=self.__set_error
        )
        
        return await self.response
    
    def __define_response(self, resp: T):
        if not self.response.done():
            self.response.set_result(resp)
        self.event.set()
    
    def __set_error(self, exc: Exception):
        if not self.response.done():
            self.response.set_exception(exc)
        
        self.event.set()