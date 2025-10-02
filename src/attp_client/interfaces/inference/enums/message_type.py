from enum import Enum


class MessageTypeEnum(Enum):
    TOOL_STATE_EVENT = 'tool_state_event'

    OPERATOR_CALLED_EVENT = 'operator_called_event'

    SYSTEM_EVENT = 'system_event'  # user is created, or added to chat or smth
    SYSTEM_MESSAGE = 'system_message'

    USER_MESSAGE = 'user_message'
    AI_MESSAGE = 'ai_message'
    #
    OPERATOR_MESSAGE = 'operator_message'
    CUSTOMER_MESSAGE = 'customer_message'

    PLACEHOLDER_MESSAGE = 'placeholder_message'  # content is the key for placeholder
