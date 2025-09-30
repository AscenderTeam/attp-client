from attp_client.types.route_mapping import AttpRouteMapping, RouteType
from attp_client.misc.fixed_basemodel import FixedBaseModel


class IRouteMapping(FixedBaseModel):
    pattern: str
    route_id: int
    route_type: RouteType
    
    @staticmethod
    def from_route_mapper(mapper: AttpRouteMapping):
        return IRouteMapping(pattern=mapper.pattern, route_id=mapper.route_id, route_type=mapper.route_type)