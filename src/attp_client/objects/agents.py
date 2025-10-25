from typing import Any

from attp_client.interfaces.objects.agent import IAgentDTO, IAgentResponse
from attp_client.misc.serializable import Serializable
from attp_client.router import AttpRouter


class AttpAgents:
    def __init__(self, router: AttpRouter) -> None:
        self.router = router

    async def create_agent(self, data: IAgentDTO) -> IAgentResponse:
        """Create a new agent."""
        response = await self.router.send("agents:create", data, expected_response=IAgentResponse)
        return response

    async def get_agent(self, agent_id: int | None = None, agent_name: str | None = None) -> IAgentResponse:
        """Get a single agent by id or by name."""
        if not agent_id and not agent_name:
            raise ValueError("You must provide either 'agent_id' or 'agent_name'.")
        if agent_id and agent_name:
            raise ValueError("Provide only one of 'agent_id' or 'agent_name', not both.")

        payload: dict[str, Any] = {}
        if agent_id is not None:
            payload["agent_id"] = agent_id
        if agent_name is not None:
            payload["agent_name"] = agent_name

        response = await self.router.send(
            "agents:get",
            Serializable[dict[str, Any]](payload),
            expected_response=IAgentResponse,
        )
        return response

    async def update_agent(self, agent_id: int, data: IAgentDTO) -> IAgentResponse:
        """Update an existing agent by id."""
        payload = Serializable[dict[str, Any]]({
            "agent_id": agent_id,
            "data": data.model_dump(mode="json"),
        })
        response = await self.router.send(
            "agents:update",
            payload,
            expected_response=IAgentResponse,
        )
        return response

    async def delete_agent(self, agent_id: int) -> None:
        """Delete an agent by id."""
        await self.router.emit("agents:delete", Serializable[dict[str, int]]({"agent_id": agent_id}))
