import asyncio
from typing import Any, Callable, MutableMapping

from attp_client.errors.attp_exception import AttpException
from attp_client.errors.not_found import NotFoundError
from attp_client.interfaces.catalogs.tools.envelope import IEnvelope
from attp_client.interfaces.error import IErr
from attp_client.tools import ToolsManager

from reactivex import operators as ops
from reactivex.scheduler.eventloop import AsyncIOScheduler

from attp_core.rs_api import PyAttpMessage


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
        
        self.responder = self.tool_manager.router.responder
    
    async def start_tool_listener(self):
        scheduler = AsyncIOScheduler(asyncio.get_event_loop())
        
        def handle_call(item: IEnvelope):
            asyncio.create_task(self.handle_call(item))
        
        def send_err(err: AttpException):
            asyncio.create_task(self.tool_manager.router.session.send_error(err=err.to_ierr(), correlation_id=None, route=1))
        
        def envelopize(item: PyAttpMessage):
            if not item.payload:
                raise AttpException("EmptyPayload", detail={"message": "Payload was empty."})
            try:
                return IEnvelope.mps(item.payload)
            except Exception as e:
                raise AttpException("InvalidPayload", detail={"message": f"Payload was invalid: {str(e)}"})

        def catch_handler(err: Any, _: Any):
            # Convert any exception to AttpException if needed
            if not isinstance(err, AttpException):
                attp_err = AttpException("UnhandledException", detail={"message": str(err)})
            else:
                attp_err = err
            send_err(attp_err)
            # Return an empty observable to terminate the stream after error
            from reactivex import empty
            return empty()

        self.responder.pipe(
            ops.filter(lambda item: item.payload is not None and item.correlation_id == 1),
            ops.map(lambda item: envelopize(item)),
            ops.catch(catch_handler),
            ops.filter(lambda item: item.catalog == self.catalog_name and item.tool_id in self.attached_tools),
            ops.observe_on(scheduler),
        ).subscribe(lambda item: handle_call(item))
    
    async def attach_tool(
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
        assigned_id = await self.tool_manager.register(
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
    
    async def detach_tool(
        self,
        name: str
    ):
        tool_id = self.tool_name_to_id_symlink.get(name)
        
        if not tool_id:
            raise NotFoundError(f"Tool {name} not marked as registered and wasn't found in the catalog {self.catalog_name}.")
        
        await self.tool_manager.unregister(self.catalog_name, tool_id)
        return tool_id
    
    async def detach_all_tools(self):
        for tool_id in list(self.attached_tools.keys()):
            await self.tool_manager.unregister(self.catalog_name, tool_id)
            del self.attached_tools[tool_id]
        
        self.tool_name_to_id_symlink.clear()
    
    async def handle_call(self, envelope: IEnvelope) -> Any:
        tool = self.attached_tools.get(envelope.tool_id)

        if not tool:
            raise NotFoundError(f"Tool {envelope.tool_id} not marked as registered and wasn't found in the catalog {self.catalog_name}.")

        return await tool(envelope)