from typing import overload
from uuid import UUID
from attp_client.interfaces.objects.chat import IChatDTO, IChatResponse
from attp_client.misc.paginated import IPaginatedResponse
from attp_client.misc.serializable import Serializable
from attp_client.router import AttpRouter
# from attp_client.session import SessionDriver
from attp_client.types.chatmode import ChatModeEnum


class AttpChats:
    def __init__(self, router: AttpRouter) -> None:
        self.router = router

    @overload
    async def create_chat(
        self,
        name: str,
        platform: str,
        mode: ChatModeEnum = ...,
    ): ...
    
    @overload
    async def create_chat(
        self,
        name: str,
        platform: str,
        mode: ChatModeEnum = ...,
        *,
        agent_name: str,
    ): ...
    
    @overload
    async def create_chat(
        self,
        name: str,
        platform: str,
        mode: ChatModeEnum = ...,
        *,
        agent_id: int,
    ): ...
    
    @overload
    async def create_chat(
        self,
        name: str,
        platform: str,
        mode: ChatModeEnum = ...,
        *,
        responsible: int,
        client_id: str | None = None,
    ): ...

    async def create_chat(
        self, 
        name: str, 
        platform: str,
        mode: ChatModeEnum = ChatModeEnum.AGENT_AUTOPILOT,
        *,
        agent_name: str | None = None,
        agent_id: int | None = None,
        responsible: int | None = None,
        client_id: str | None = None,
    ):
        if agent_name and agent_id:
            raise ValueError("You can only provide either 'agent_name' or 'agent_id', not both.")

        if not agent_name and not agent_id:
            raise ValueError("You must provide either 'agent_name' or 'agent_id'.")

        payload = IChatDTO(
            name=name,
            mode=mode,
            platform=platform,
            agent_name=agent_name,
            agent_id=agent_id,
            responsible=responsible,
            client_id=client_id,
        )

        response = await self.router.send("chats:create", payload, expected_response=IChatResponse)
        
        return response
    
    async def get_chats(self):
        response = await self.router.send("chats:list", expected_response=IPaginatedResponse[IChatResponse])
        
        return response
    
    async def get_chat(self, chat_id: UUID):
        response = await self.router.send("chats:specific", Serializable[dict[str, UUID]]({"chat_id": chat_id}), expected_response=IChatResponse)
        
        return response
    
    async def delete_chat(self, chat_id: UUID):
        await self.router.emit("chats:delete", Serializable[dict[str, UUID]]({"chat_id": chat_id}))

    async def change_agent(self, chat_id: UUID, new_agent_id: int):
        await self.router.emit("chats:agent", Serializable[dict[str, UUID | int]]({"chat_id": chat_id, "new_agent_id": new_agent_id}))
    
    