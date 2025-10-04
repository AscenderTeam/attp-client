from typing import Any, Sequence
from uuid import UUID
from attp_client.misc.serializable import Serializable
from attp_client.router import AttpRouter
from attp_client.session import SessionDriver


class ToolsManager:
    def __init__(self, router: AttpRouter) -> None:
        self.router = router
    
    async def register(
        self, 
        catalog_name: str,
        name: str, 
        description: str | None = None,
        schema_id: str | None = None,
        schema: dict | None = None,
        *,
        return_direct: bool = False,
        schema_ver: str = "1.0",
        timeout_ms: float = 20000,
        idempotent: bool = False,
        configs: Any | None = None
    ) -> UUID:
        response = await self.router.send(
            "tools:register",
            Serializable[dict[str, Any]]({
                "catalog": catalog_name,
                "tool": {
                    "name": name,
                    "description": description,
                    "schema_id": schema_id,
                    "return_direct": return_direct,
                    "schema_ver": schema_ver,
                    "schema": schema,
                    "timeout_ms": timeout_ms,
                    "idempotent": idempotent,
                    "config": configs or {}
                }
            }),
            timeout=30,
            expected_response=dict[str, Any]
        )
        
        return UUID(hex=response["assigned_id"])
    
    async def unregister(
        self,
        catalog_name: str,
        tool_id: str | Sequence[str]
    ) -> str | list[str]:
        response = await self.router.send(
            "tools:unregister",
            Serializable[dict[str, Any]]({
                "catalog": catalog_name,
                "tool_id": tool_id
            }),
            timeout=30,
            expected_response=dict[str, Any]
        )

        return response["removed_ids"]