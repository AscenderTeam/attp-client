from typing import Annotated
from pydantic import Field
from typing_extensions import Doc

from attp_client.interfaces.route_mappings import IRouteMapping
from attp_client.misc.fixed_basemodel import FixedBaseModel


class IHello(FixedBaseModel):
    proto: Annotated[str, Doc("Protocol ID")] = Field("ATTP")
    ver: Annotated[str, Doc("Semver for example: 1.0")] = Field("1.0")
    caps: Annotated[list[str], Doc("Capability flags e.g. ['schemas/json', 'stream', 'hb']")] = Field(default_factory=list)
    mapping: Annotated[list[IRouteMapping], Doc("Router pattern mappings, ATTP for optimization uses numbers and IDs for routing requests instead of human friendly patterns")] 