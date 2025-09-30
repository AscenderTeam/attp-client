from typing import Any, Callable, MutableMapping
from attp_client.errors.not_found import NotFoundError
from attp_client.tools import ToolsManager


class AttpCatalog:
    attached_tools: MutableMapping[str, Callable[..., Any]]
    tool_name_to_id_symlink: MutableMapping[str, str]
    
    def __init__(
        self,
        id: int,
        catalog_name: str,
        manager: ToolsManager
    ) -> None:
        self.id = id
        self.catalog_name = catalog_name
        self.tool_manager = manager
        self.attached_tools = {}
        self.tool_name_to_id_symlink = {}
    
    async def attach_tool(
        self,
        callback: Callable[..., Any],
        name: str, 
        description: str | None = None,
        schema_id: str | None = None,
        *,
        return_direct: bool = False,
        schema_ver: str = "1.0",
        timeout_ms: float = 20000,
        idempotent: bool = False
    ):
        assigned_id = await self.tool_manager.register(
            self.catalog_name,
            name=name,
            description=description,
            schema_id=schema_id,
            return_direct=return_direct,
            schema_ver=schema_ver,
            timeout_ms=timeout_ms,
            idempotent=idempotent
        )
        
        self.attached_tools[str(assigned_id)] = callback
        self.tool_name_to_id_symlink[name] = str(assigned_id)
        return assigned_id
    
    async def detatch_tool(
        self,
        name: str
    ):
        tool_id = self.tool_name_to_id_symlink.get(name)
        
        if not tool_id:
            raise NotFoundError(f"Tool {name} not marked as registered and wasn't found in the catalog {self.catalog_name}.")
        
        await self.tool_manager.unregister(self.catalog_name, tool_id)
        return tool_id