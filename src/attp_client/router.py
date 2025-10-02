import asyncio
from contextvars import ContextVar
from typing import Any, TypeVar, overload
import msgpack
from pydantic import TypeAdapter
from reactivex import Subject, defer, empty, from_future, of, operators as ops, throw, timer
from reactivex.scheduler.eventloop import AsyncIOScheduler
from attp_core.rs_api import PyAttpMessage, AttpCommand

from attp_client.errors.correlated_rpc_exception import CorrelatedRPCException
from attp_client.errors.serialization_error import SerializationError
from attp_client.interfaces.error import IErr
from attp_client.misc.fixed_basemodel import FixedBaseModel
from attp_client.misc.serializable import Serializable
from attp_client.session import SessionDriver
from attp_client.utils.context_awaiter import ContextAwaiter


T = TypeVar("T")


class AttpRouter:
    def __init__(
        self, 
        responder: Subject[PyAttpMessage],
        session: SessionDriver
    ) -> None:
        self.responder = responder
        self.session = session
        self.context = ContextVar[str | None]("session_context", default=None)
    
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
        # correlation_id = await self.session.send_message(pattern, data)
        
        responder = ContextAwaiter[Any](defer(
            lambda _: (
                from_future(asyncio.ensure_future(self.session.send_message(route=route, data=data))).pipe(
                    ops.flat_map(
                        lambda cid: empty().pipe(
                            ops.concat(self.__pipe_filter(cid, timeout=timeout)),
                        )
                    )
                )
            )
        ))
        
        response_data = await responder.wait()
        
        return self.__format_response(expected_type=expected_response or Any, response_data=response_data)
    
    async def emit(self, route: str, data: FixedBaseModel | Serializable | None = None):
        await self.session.emit_message(route, data)
    
    def __pipe_filter(self, awaiting_correlation_id: bytes, timeout: float):
        loop = asyncio.get_event_loop()
        asyncio_scheduler = AsyncIOScheduler(loop)
        print(awaiting_correlation_id)
        return self.responder.pipe(
            ops.subscribe_on(asyncio_scheduler),
            ops.filter(lambda pair: pair.correlation_id == awaiting_correlation_id),
            ops.flat_map(lambda r: throw(CorrelatedRPCException.from_err_object(correlation_id=r.correlation_id or b'<nocorrid>', err=IErr.mps(r.payload) if r.payload else IErr(detail={"code": "ErrorWithoutPayload"}))) if r.command_type == AttpCommand.ERR else of(r)),
            #######################################
            ##     This is RPC Defer Handler     ##
            #######################################
            ops.timeout_with_mapper(
                timer(timeout, scheduler=asyncio_scheduler),
                lambda i: (
                    timer(timeout, scheduler=asyncio_scheduler) if getattr(i, "frame_type", None) == AttpCommand.DEFER else of(None)
                ),
                throw(TimeoutError("ATTP response failed."))
            ),
            ops.filter(lambda pair: pair.command_type == AttpCommand.ACK),
            ops.first(),
        )

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