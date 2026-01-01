from typing import Any, Callable, MutableMapping
from uuid import UUID

from attp_client.errors.attp_exception import AttpException
from attp_client.errors.not_found import NotFoundError
from attp_client.interfaces.catalogs.tools.envelope import IEnvelope
from attp_client.tools import ToolsManager


class AttpCatalog:
    attached_tools: MutableMapping[str, Callable[..., Any]] # id, callback
    tool_name_to_id_symlink: MutableMapping[str, str] # name, id
    
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
    
    async def handle_callback(self, envelope: IEnvelope) -> Any:
        if envelope.tool_id not in self.attached_tools:
            raise NotFoundError(f"Tool {envelope.tool_id} not marked as registered and wasn't found in the catalog {self.catalog_name}.")

        try:
            result = await self.handle_call(envelope)
        except AttpException as e:
            return e.to_ierr()
        
        return result

    def attach_tool(
        self,
        callback: Callable[[IEnvelope], Any],
        name: str, 
        description: str | None = None,
        schema: dict | None = None,
        schema_id: str | None = None,
        *,
        return_direct: bool = False,
        schema_ver: str = "1.0",
        timeout_ms: float = 20000,
        idempotent: bool = False
    ):
        assigned_id = self.tool_manager.register(
            self.catalog_name,
            name=name,
            description=description,
            schema_id=schema_id,
            return_direct=return_direct,
            schema=schema,
            schema_ver=schema_ver,
            timeout_ms=timeout_ms,
            idempotent=idempotent
        )
        
        self.attached_tools[str(assigned_id)] = callback
        self.tool_name_to_id_symlink[name] = str(assigned_id)
        return assigned_id
    
    def detach_tool(
        self,
        name: str
    ):
        tool_id = self.tool_name_to_id_symlink.get(name)
        
        if not tool_id:
            raise NotFoundError(f"Tool {name} not marked as registered and wasn't found in the catalog {self.catalog_name}.")
        
        self.tool_manager.unregister(self.catalog_name, UUID(tool_id))
        return tool_id
    
    def detach_all_tools(self):
        for tool_id in list(self.attached_tools.keys()):
            self.tool_manager.unregister(self.catalog_name, UUID(tool_id))
            del self.attached_tools[tool_id]
        
        self.tool_name_to_id_symlink.clear()
    
    async def handle_call(self, envelope: IEnvelope) -> Any:
        tool = self.attached_tools.get(envelope.tool_id)

        if not tool:
            raise NotFoundError(f"Tool {envelope.tool_id} not marked as registered and wasn't found in the catalog {self.catalog_name}.")

        return await tool(envelope)
