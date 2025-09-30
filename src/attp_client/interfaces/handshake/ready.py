from typing import Annotated, Sequence
from typing_extensions import Doc

from attp_client.interfaces.route_mappings import IRouteMapping
from attp_client.misc.fixed_basemodel import FixedBaseModel


class IReady(FixedBaseModel):
    session: Annotated[str, Doc("Server-issued session id (per connection)")] # REQUIRED
    server_time: Annotated[str | None, Doc("Server ISO time for skew hints")] = None
    server_routes: Sequence[IRouteMapping]