from dataclasses import dataclass
from typing import Any, Literal, TypeAlias

# from core.attp.interfaces.handshake.mapping import IRouteMapping

RouteType: TypeAlias = Literal["event", "message", "err", "disconnect", "connect"]


@dataclass(frozen=True, unsafe_hash=True)
class AttpRouteMapping:
    pattern: str
    route_id: int
    route_type: RouteType
    callback: Any