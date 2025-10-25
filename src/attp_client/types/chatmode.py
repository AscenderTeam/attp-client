from enum import Enum


class ChatModeEnum(Enum):
    AGENT_AUTOPILOT = "agent_autopilot"
    AGENT_CO_PILOT = "agent_copilot"
    PRIVATE_SINGLE = "private_single"
    PRIVATE_GROUP = "private_group"