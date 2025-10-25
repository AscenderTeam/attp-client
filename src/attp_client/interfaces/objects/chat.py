from uuid import UUID
from attp_client.misc.fixed_basemodel import FixedBaseModel
from attp_client.types.chatmode import ChatModeEnum


class IChatDTO(FixedBaseModel):
    name: str
    mode: ChatModeEnum
    platform: str
    agent_name: str | None = None
    agent_id: int | None = None
    responsible: int | None = None
    client_id: str | None = None
    

class IChatResponse(IChatDTO):
    id: UUID