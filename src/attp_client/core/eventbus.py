import traceback
from typing import TYPE_CHECKING, Any, Callable, Set

from pydantic import ValidationError, validate_call

from attp_client.core.utils.callbacks import execute_call, execute_event
from attp_client.errors.attp_exception import AttpException
from attp_client.interfaces.error import IErr
from attp_client.session import SessionDriver
from attp_client.types.route_mapping import AttpRouteMapping, RouteType

if TYPE_CHECKING:
    from attp_client.router import AttpRouter

from attp_core.rs_api import PyAttpMessage, AttpCommand


class AttpEventBus:
    routes: Set[AttpRouteMapping]
    
    def __init__(self, router: "AttpRouter") -> None:
        self.routes = set()
        self.increment_index = 2
        self.router = router
    
    async def subscribe(
        self,
        route_type: RouteType,
        pattern: str,
        callback: Callable[..., Any]
    ):
        if pattern == "connect" and route_type == "connect":
            self.routes.add(AttpRouteMapping(
                pattern=pattern,
                route_id=0,
                route_type=route_type,
                callback=validate_call(config={"arbitrary_types_allowed": True})(callback)
            ))
            return
        
        if pattern == "disconnect" and route_type == "disconnect":
            self.routes.add(AttpRouteMapping(
                pattern=pattern,
                route_id=0,
                route_type=route_type,
                callback=validate_call(config={"arbitrary_types_allowed": True})(callback)
            ))
            return
        
        self.routes.add(AttpRouteMapping(
            pattern=pattern,
            route_id=self.increment_index,
            route_type=route_type,
            callback=validate_call(config={"arbitrary_types_allowed": True})(callback)
        ))
        self.increment_index += 1
    
    async def emit(self, session: SessionDriver, message: PyAttpMessage):
        if message.command_type not in (AttpCommand.EMIT, AttpCommand.CALL, AttpCommand.ERR):
            return
        
        try:   
            relevant_route = next(
                (route for route in self.routes if route.route_id == message.route_id),
                None
            )
            
            if message.command_type == AttpCommand.CALL:
                if not relevant_route:
                    assert message.correlation_id
                    await self.router.session.send_error(
                        IErr(detail={"code": "NotFound", "message": "Route not found."}), 
                        message.correlation_id, 
                        message.route_id or 0
                    )
                    return
                await execute_call(message, relevant_route, session=self.router.session)
            
            if message.command_type == AttpCommand.EMIT:
                if not relevant_route:
                    return
                
                await execute_event(message, relevant_route)
            # TODO: Implement error callback
            # Conditions to fire the callback, if err callback has specific route_id, fire it if frame has same route_id, if it doesn't (route_id is 1) then fire all relevant_routes.
            # If `message` frame has correlation_id then we should skip if (if route_ids won't match)
        except ValidationError as e:
            traceback.print_exc()
            await session.send_error(IErr(detail={"code": "ValidationError", "data": str(e)}), correlation_id=message.correlation_id, route=message.route_id)
        
        except AttpException as e:
            traceback.print_exc()
            await session.send_error(e.to_ierr(), correlation_id=message.correlation_id, route=message.route_id)
        
        except Exception:
            traceback.print_exc()
            await session.send_error(IErr(detail={"code": "InternalExecutionError", "data": traceback.format_exc()}), correlation_id=message.correlation_id, route=message.route_id)