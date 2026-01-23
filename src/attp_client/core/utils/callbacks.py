from typing import TYPE_CHECKING, Any

import msgpack
from attp_client.core.utils.executor import execute_validated
from attp_client.misc.fixed_basemodel import FixedBaseModel
from attp_client.misc.serializable import Serializable
from attp_client.types.route_mapping import AttpRouteMapping
from attp_core.rs_api import PyAttpMessage, AttpCommand

from attp_client.utils.stream_object import StreamObject

if TYPE_CHECKING:
    from attp_client.session import SessionDriver


async def execute_call(
    frame: PyAttpMessage, 
    mapping: AttpRouteMapping,
    *, session: "SessionDriver"
):
    callback = mapping.callback
    
    payload = {}
    
    if frame.payload:
        payload = msgpack.unpackb(frame.payload)
    
    response = await execute_validated(callback, payload, frame=frame)
    
    if isinstance(response, StreamObject):
        iterable = response.iterate()
        if not iterable:
            return

        assert frame.correlation_id
        await session.respond_stream(
            route=frame.route_id,
            correlation_id=frame.correlation_id,
            command_type=AttpCommand.STREAMBOS,
        )

        if response.is_async:
            async for chunk in iterable:  # type: ignore
                await session.respond_stream(
                    route=frame.route_id,
                    correlation_id=frame.correlation_id,
                    payload=chunk,
                    command_type=AttpCommand.CHUNK,
                )
        else:
            for chunk in iterable:  # type: ignore
                await session.respond_stream(
                    route=frame.route_id,
                    correlation_id=frame.correlation_id,
                    payload=chunk,
                    command_type=AttpCommand.CHUNK,
                )

        await session.respond_stream(
            route=frame.route_id,
            correlation_id=frame.correlation_id,
            command_type=AttpCommand.STREAMEOS,
        )
        return

    if not isinstance(response, FixedBaseModel) and not isinstance(response, Serializable):
        response = Serializable[Any](data=response)
    
    assert frame.correlation_id
    await session.respond(route=frame.route_id, correlation_id=frame.correlation_id, payload=response)


async def execute_event(
    frame: PyAttpMessage,
    mapping: AttpRouteMapping
):
    callback = mapping.callback
    
    payload = {}
    
    if frame.payload:
        payload = msgpack.unpackb(frame.payload)
    
    await execute_validated(callback, payload, frame=frame)
