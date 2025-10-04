from logging import Logger, getLogger
from typing import Any, Sequence
from uuid import UUID
from attp_client.interfaces.inference.message import IMessageResponse, IMessageDTOV2
from attp_client.misc.serializable import Serializable
from attp_client.router import AttpRouter


class AttpInferenceAPI:
    """
    AttpInferenceAPI provides methods to interact with the inference API of the AgentHub.
    """
    def __init__(
        self,
        router: AttpRouter,
        logger: Logger = getLogger("Ascender Framework")
    ) -> None:
        self.router = router
        self.logger = logger
    
    async def create_chat(
        self,
        name: str,
        agent_id: int | None = None,
        agent_name: str | None = None,
        mode: str = "agent_autopilot",
        platform: str = "unknown",
        responsible: int | None = None,
        client_id: str | None = None,
        created_by_id: int | None = None,
        timeout: float = 30
    ):
        """
        Create chat for inference.
        TODO: Implement own chat manager for chats, just like I did with catalogs.
        """
        response = await self.router.send(
            "messages:chat:create",
            Serializable[dict[str, Any]]({
                "name": name,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "mode": mode,
                "platform": platform,
                "responsible": responsible,
                "client_id": client_id,
                "created_by_id": created_by_id
            }),
            timeout=timeout,
            expected_response=dict[str, Any]
        )
        
        return response
    
    async def invoke_inference(
        self,
        agent_id: int | None = None,
        agent_name: str | None = None,
        *,
        input_configuration: dict[str, Any] | None = None,
        messages: Sequence[IMessageDTOV2] | None = None,
        stream: bool = False,
        timeout: float = 200
    ) -> IMessageResponse:
        """
        Invoke inference for a specific agent by its ID or name.
    
        Parameters
        ----------
        agent_id : int | None, optional
            The ID of the agent to invoke inference for, by default None
        agent_name : str | None, optional
            The name of the agent to invoke inference for, by default None
            _description_, by default None
        input_configuration : dict[str, Any] | None, optional
            The configuration for the input, by default None
        messages : Sequence[IMessageDTOV2] | None, optional
            The messages to include in the inference, by default None
        stream : bool, optional
            Whether to stream the response, by default False
        timeout : float, optional
            The timeout for the request, by default 200

        Returns
        -------
        IMessageResponse
            The response from the inference request.

        Raises
        ------
        ValueError
            If neither 'agent_id' nor 'agent_name' is provided.
        ValueError
            If both 'agent_id' and 'agent_name' are provided.
        """
        
        if not agent_id and not agent_name:
            raise ValueError("Required at least one identification specifier, 'agent_id' or 'agent_name'")
        
        if agent_id and agent_name:
            raise ValueError("Cannot find agent by two identification specifiers, use only one!")
        
        response = await self.router.send("messages:inference:invoke", Serializable[dict[str, Any]]({
            "agent_id": agent_id,
            "agent_name": agent_name,
            "input_configuration": input_configuration,
            "messages": [message.model_dump(mode="json") for message in (messages or [])],
            "stream": stream
        }), timeout=timeout, expected_response=IMessageResponse)
        
        return response
    
    async def invoke_chat_inference(
        self, 
        messages: Sequence[IMessageDTOV2], 
        chat_id: UUID,
        stream: bool = False,
        timeout: float = 200,
    ) -> IMessageResponse:
        """
        Invoke inference for a specific chat by its chat_id.

        Parameters
        ----------
        messages : Sequence[IMessageDTOV2]
            The messages to include in the inference.
        chat_id : UUID
            The ID of the chat to invoke inference for.
        stream : bool, optional
            Whether to stream the response, by default False.
        timeout : float, optional
            The timeout for the request, by default 200.

        Returns
        -------
        IMessageResponse
            The response from the inference request.
        """
        for message in messages:
            await self.router.send("messages:append", message, timeout=5)
        
        response = await self.router.send(
            "messages:chat:invoke", 
            Serializable[dict[str, Any]]({
                "chat_id": str(chat_id),
                "stream": stream
            }),
            timeout=timeout,
            expected_response=IMessageResponse
        )
        
        return response

    async def append_message(self, message: IMessageDTOV2 | Sequence[IMessageDTOV2]) -> None:
        """
        Append a message or a sequence of messages to the current chat.
        
        Parameters
        ----------
        message : IMessageDTOV2 | Sequence[IMessageDTOV2]
            The message or messages to append.
        """
        if isinstance(message, Sequence):
            for msg in message:
                await self.router.emit("messages:append", msg)
        else:
            await self.router.emit("messages:append", message)