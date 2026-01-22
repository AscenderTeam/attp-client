from contextvars import ContextVar
from typing import Any, AsyncIterable, Callable, TypeVar, overload
import msgpack
from uuid import uuid4
from pydantic import TypeAdapter
from attp_core.rs_api import PyAttpMessage

from attp_client.core.ack_gate import StatefulAckGate
from attp_client.errors.dead_session import DeadSessionError
from attp_client.errors.serialization_error import SerializationError
from attp_client.misc.fixed_basemodel import FixedBaseModel
from attp_client.misc.serializable import Serializable
from attp_client.session import SessionDriver
from attp_client.utils.stream_receiver import StreamReceiver


T = TypeVar("T")
S = TypeVar("S")


class AttpRouter:
    def __init__(
        self,
        session: SessionDriver
    ) -> None:
        self.session = session
        self.context = ContextVar[str | None]("session_context", default=None)
        self.ack_gate = StatefulAckGate()
    
    def convert_message(self, expected_type: type[T], message: PyAttpMessage) -> T | Any:
        response = self.__format_response(expected_type=expected_type, response_data=message)
        return response
    
    @overload
    async def send(
        self,
        route: str,
        data: FixedBaseModel | Serializable | None = ...,
        timeout: float = 20,
    ) -> Any: ...
    
    @overload
    async def send(
        self, 
        route: str,
        data: FixedBaseModel | Serializable | None = ...,
        timeout: float = 20, *,
        expected_response: type[T],
    ) -> T | Any: ...
    
    async def send(
        self, 
        route: str, 
        data: FixedBaseModel | Serializable | None = None,
        timeout: float = 50, *,
        expected_response: type[T] | None = None
    ) -> T | Any:
        if not self.session.is_connected:
            raise DeadSessionError(self.session.organization_id)

        correlation_id = uuid4().bytes
        queue = await self.ack_gate.request_ack(correlation_id)
        try:
            await self.session.send_message(route=route, data=data, correlation_id=correlation_id)
            response_data = await self.ack_gate.wait_for_ack(correlation_id, timeout, queue=queue)
        finally:
            await self.ack_gate.complete_ack(correlation_id)
        
        return self.__format_response(expected_type=expected_response or Any, response_data=response_data)
    
    @overload
    async def request_stream(
        self,
        route: str,
        data: FixedBaseModel | Serializable | None = ...,
        timeout: float = 50,
        *,
        formatter: Callable[[PyAttpMessage], S | None],
    ) -> AsyncIterable[S]: ...

    @overload
    async def request_stream(
        self,
        route: str,
        data: FixedBaseModel | Serializable | None = ...,
        timeout: float = 50,
        *,
        formatter: None = ...,
    ) -> AsyncIterable[Any]: ...

    async def request_stream(
        self,
        route: str,
        data: FixedBaseModel | Serializable | None = None,
        timeout: float = 50,
        *,
        formatter: Callable[[PyAttpMessage], S | None] | None = None,
    ) -> AsyncIterable[Any] | AsyncIterable[S]:
        if not self.session.is_connected:
            raise DeadSessionError(self.session.organization_id)

        correlation_id = uuid4().bytes
        queue = await self.ack_gate.request_ack(correlation_id)
        try:
            await self.session.send_message(route=route, data=data, correlation_id=correlation_id)
        except Exception:
            await self.ack_gate.complete_ack(correlation_id)
            raise

        async def _stream():
            try:
                async for frame in self.ack_gate.stream_ack(correlation_id, timeout, queue=queue):
                    yield frame
            finally:
                await self.ack_gate.complete_ack(correlation_id)

        stream = StreamReceiver(_stream(), formatter=formatter)
        
        return stream
        
    
    async def emit(self, route: str, data: FixedBaseModel | Serializable | None = None):
        if not self.session.is_connected:
            raise DeadSessionError(self.session.organization_id)
        
        await self.session.emit_message(route, data)

    async def handle_response(self, message: PyAttpMessage) -> None:
        if not message.correlation_id:
            return
        await self.ack_gate.feed(message)

    def __format_response(self, expected_type: Any, response_data: PyAttpMessage):
        if issubclass(expected_type, FixedBaseModel):
            if not response_data.payload:
                raise SerializationError(f"Nonetype payload received from session while expected type {expected_type.__name__}")
            try:
                return expected_type.mps(response_data.payload)
            except Exception as e:
                raise SerializationError(str(e))
        
        serialized = msgpack.unpackb(response_data.payload) if response_data.payload else None
        
        if expected_type is not None:
            return serialized
        
        return TypeAdapter(expected_type, config={"arbitrary_types_allowed": True}).validate_python(serialized)
