from typing import Any, Literal
from uuid import UUID
from attp_client.interfaces.inference.enums.message_emergency_type import MessageEmergencyTypeEnum
from attp_client.interfaces.inference.enums.message_type import MessageTypeEnum
from attp_client.interfaces.inference.tool import ToolV2
from attp_client.misc.fixed_basemodel import FixedBaseModel


class BaseMessage(FixedBaseModel):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

class IAttachmentDTO(BaseMessage):
    file_id: int

class IMessageDTOV2(FixedBaseModel):
    """
    The DTO Object of Message in AgentHub, contains message content and tool execution data.
    """
    content: dict | str | None
    message_type: MessageTypeEnum
    attachments: list[IAttachmentDTO] | None = None

    reply_to_message_id: int | None = None
    chat_id: UUID
    agent_id: int | None = None
    user_id: int | None = None
    client_id: str | None = None

    tool_called: ToolV2 | None = None
    tool_status: Literal['started', 'finished', 'error'] | None = None
    tool_started_input: str | None = None
    tool_finished_output: str | None = None
    tool_error_detail: str | None = None

    specialist_required: MessageEmergencyTypeEnum | None = None
    metadata: dict[str, Any] | None = None

    def to_wrap(self) -> dict:
        w = self.model_dump()
        del w['attachments']

        return w


class IMessageResponse(IMessageDTOV2):
    """
    Response model of AgentHub Message, it represents [MessageDTO](agenthub/dtos/message_dto.py).
    But it contains additional value as ID
    """
    id: int
    """ID of Message in database"""