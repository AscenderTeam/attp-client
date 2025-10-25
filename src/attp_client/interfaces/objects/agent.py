from typing import Any

from attp_client.misc.fixed_basemodel import FixedBaseModel


class IAgentDTO(FixedBaseModel):
    """
    A shared DTO (Data Transfer Object) for Agents.
    """
    name: str
    avatar_url: str | None = None
    description: str
    module_id: str
    configurations: dict[str, Any] = {}


class IAgentResponse(IAgentDTO):
    id: int
