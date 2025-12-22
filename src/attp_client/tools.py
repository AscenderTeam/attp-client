from collections import defaultdict
from typing import Any, Sequence
from uuid import UUID, uuid4
from attp_client.errors.not_found import NotFoundError
from attp_client.interfaces.catalogs.tools.tool import ITool
from attp_client.misc.serializable import Serializable
from attp_client.router import AttpRouter


class ToolsManager:
    tools: dict[str, list[ITool]] # catalog_name, tool
    
    def __init__(self, router: AttpRouter) -> None:
        self.router = router
        self.tools = defaultdict(list)
    
    def register(
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
        tool_id = uuid4()
        
        self.tools[catalog_name].append(ITool(
            id=tool_id,
            name=name,
            description=description,
            schema_id=schema_id,
            return_direct=return_direct,
            schema=schema,
            schema_ver=schema_ver,
            timeout_ms=timeout_ms,
            idempotent=idempotent,
            config=configs,
            catalog=catalog_name
        ))
        
        return tool_id
    
    def unregister(
        self,
        catalog_name: str,
        tool_id: UUID | Sequence[UUID]
    ) -> UUID | list[UUID]:
        if catalog_name not in self.tools:
            raise NotFoundError(f"Catalog {catalog_name} not found in the tools manager.")
        
        if isinstance(tool_id, UUID):
            if str(tool_id) in [str(t.id) for t in self.tools[catalog_name]]:
                self.tools[catalog_name] = [
                    t for t in self.tools[catalog_name] if str(t.id) != str(tool_id)
                ]
                return tool_id
            raise NotFoundError(f"Tool {tool_id} not found in the catalog {catalog_name}.")
        
        removed_ids = []
        for tid in tool_id:
            if str(tid) in [str(t.id) for t in self.tools[catalog_name]]:
                self.tools[catalog_name] = [
                    t for t in self.tools[catalog_name] if str(t.id) != str(tid)
                ]
                removed_ids.append(tid)
        
        return removed_ids
    
    def get_tools(self, catalog_name: str) -> list[ITool]:
        return self.tools.get(catalog_name, [])
    
    def get_tool(self, catalog_name: str, tool_id: UUID) -> ITool:
        # Use next(...) to find the tool with the matching id
        tool = next((t for t in self.tools.get(catalog_name, []) if str(t.id) == str(tool_id)), None)
        
        if tool:
            return tool
        
        raise NotFoundError(f"Tool {tool_id} not found in the catalog {catalog_name}.")