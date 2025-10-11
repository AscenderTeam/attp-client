import asyncio
from functools import cached_property
from logging import Logger, getLogger
from typing import Any, Callable
from attp_core.rs_api import AttpClientSession, Limits
from reactivex import Subject, operators as ops
from reactivex.scheduler.eventloop import AsyncIOScheduler
from attp_core.rs_api import PyAttpMessage

from attp_client.catalog import AttpCatalog
from attp_client.errors.dead_session import DeadSessionError
from attp_client.inference import AttpInferenceAPI
from attp_client.interfaces.catalogs.catalog import ICatalogResponse
from attp_client.interfaces.error import IErr
from attp_client.misc.serializable import Serializable
from attp_client.router import AttpRouter
from attp_client.session import SessionDriver
from attp_client.tools import ToolsManager
from attp_client.types.route_mapping import AttpRouteMapping, RouteType
from attp_client.utils import envelopizer

from attp_core.rs_api import AttpCommand

class ATTPClient:
    
    is_connected: bool
    client: AttpClientSession
    session: SessionDriver | None
    routes: list[AttpRouteMapping]
    inference: AttpInferenceAPI
    catalogs: list[AttpCatalog]

    def __init__(
        self,
        agt_token: str,
        organization_id: int,
        *,
        connection_url: str | None = None,
        max_retries: int = 20,
        limits: Limits | None = None,
        logger: Logger | None = None
    ):
        self.__agt_token = agt_token
        self.organization_id = organization_id
        self.connection_url = connection_url or "attp://localhost:6563"
        
        self.session = None
        self.max_retries = max_retries
        self.limits = limits or Limits(max_payload_size=50000)
        self.client = AttpClientSession(self.connection_url, limits=self.limits)
        self.logger = logger
        
        self.route_increment_index = 2
        
        self.responder = Subject[PyAttpMessage]()
        self.routes = []
        self.catalogs = []
        self.disposable = None
    
    async def connect(self):
        # Open the connection
        client = await self.client.connect(self.max_retries)
        
        if not client.session:
            raise ConnectionError("Failed to connect to ATTP server after 10 attempts!")
        
        self.session = SessionDriver(
            client.session, 
            agt_token=self.__agt_token, 
            organization_id=self.organization_id,
            # route_mappings=self.routes,
            logger=self.logger or getLogger("Ascender Framework")
        )
        asyncio.create_task(self.session.start_listener())
        # Send an authentication frame as soon as connection estabilishes with agenthub
        await self.session.authenticate(self.routes)
        asyncio.create_task(self.session.listen(self.responder))
        
        self.router = AttpRouter(self.responder, self.session)
        self.inference = AttpInferenceAPI(self.router)
        
        self.add_event_handler("tools:call", "message", self._tool_callback)
        
        
        
        self.disposable = self.responder.pipe(
            ops.subscribe_on(AsyncIOScheduler(asyncio.get_event_loop())),
        ).subscribe(
            on_next=lambda item: self.logger.debug(f"Received message on route {item.route_id} with correlation ID {item.correlation_id}"),
            on_error=lambda e: self.logger.error(f"Error in responder stream: {e}"),
        )

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None
            self.is_connected = False

    @cached_property
    def tools(self):
        return ToolsManager(self.router)
    
    async def catalog(self, catalog_name: str):
        if any(c.catalog_name == catalog_name for c in self.catalogs):
            return next(c for c in self.catalogs if c.catalog_name == catalog_name)
        
        catalog = await self.router.send(
            "tools:catalogs:specific", 
            Serializable[dict[str, str]]({"catalog_name": catalog_name}),
            timeout=10,
            expected_response=ICatalogResponse
        )
        self.catalogs.append(
            AttpCatalog(id=catalog.catalog_id, catalog_name=catalog_name, manager=self.tools)
        )
        
        await self.catalogs[-1].start_tool_listener()

        return self.catalogs[-1] # Return the newly added catalog

    async def close_catalog(self, catalog: AttpCatalog):
        await catalog.detach_all_tools()
        self.catalogs.remove(catalog)

    async def _tool_callback(self, message: PyAttpMessage):
        if not self.session:
            raise DeadSessionError(self.organization_id)
        
        if not message.correlation_id:
            await self.session.send_error(IErr(
                detail={"message": "Correlation ID was missing in the message.", "code": "MissingCorrelationId"},
            ))
            return
        
        print("TOOL CALLBACK MESSAGE:", message.payload)
        try:
            envelope = envelopizer.envelopize(message)
        except ValueError as e:
            await self.session.send_error(IErr(
                detail={"message": str(e), "code": "InvalidPayload"},
            ))
            return

        catalog = next((c for c in self.catalogs if c.id == envelope.tool_id), None)
        if not catalog:
            await self.session.send_error(IErr(
                detail={"message": f"Catalog with id {envelope.tool_id} not found.", "code": "NotFoundError"},
            ))
            return

        response = await catalog.handle_callback(envelope)

        await self.session.respond(route=message.route_id, correlation_id=message.correlation_id, payload=response)

    async def _handle_incoming(self, message: PyAttpMessage):
        relevant_route = next((route for route in self.routes if route.route_id == message.route_id), None)
        
        if not relevant_route:
            if self.logger:
                self.logger.warning(f"Received message for unknown route ID {message.route_id}. Ignoring.")
            return
        
        response = await relevant_route.callback(message)
        
        if message.command_type == AttpCommand.CALL:
            if not self.session:
                raise DeadSessionError(self.organization_id)
            
            if not message.correlation_id:
                await self.session.send_error(IErr(
                    detail={"message": "Correlation ID was missing in the message.", "code": "MissingCorrelationId"},
                ))
                return
            
            await self.session.respond(
                route=message.route_id,
                correlation_id=message.correlation_id,
                payload=response
            )
    
    def add_event_handler(
        self, 
        pattern: str, 
        route_type: RouteType,
        callback: Callable[..., Any],
    ):
        if route_type in ["connect", "disconnect"]:
            self.routes.append(
                AttpRouteMapping(
                    pattern=pattern,
                    route_id=0,
                    route_type=route_type,
                    callback=callback
                )
            )
            return
        
        self.routes.append(
            AttpRouteMapping(
                pattern=pattern, 
                route_id=self.route_increment_index, 
                route_type=route_type, 
                callback=callback
            )
        )
        
        self.route_increment_index += 1