from typing import Sequence

from attp_client.errors.not_found import NotFoundError
from attp_client.interfaces.route_mappings import IRouteMapping

from attp_client.types.route_mapping import RouteType


def resolve_route_by_id(route_type: RouteType, pattern: str, route_mapping: Sequence[IRouteMapping]):
    route = next(
        (route for route in route_mapping if route.pattern == pattern and route.route_type == route_type),
        None
    )
    
    if not route:
        raise NotFoundError(f"Route {pattern} not found.")
    
    return route