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
from attp_client.misc.fixed_basemodel import FixedBaseModel
from attp_client.misc.serializable import Serializable
from attp_client.objects.agents import AttpAgents
from attp_client.objects.chats import AttpChats
from attp_client.router import AttpRouter
from attp_client.session import SessionDriver
from attp_client.tools import ToolsManager
from attp_client.types.route_mapping import AttpRouteMapping, RouteType
from attp_client.utils import envelopizer

from attp_core.rs_api import AttpCommand, init_logging

from attp_client.utils.stream_object import StreamObject
from attp_client.utils.trigger_callable import trigger_callable


class ATTPClient:
    
    is_connected: bool
    client: AttpClientSession
    session: SessionDriver | None
    routes: list[AttpRouteMapping]
    inference: AttpInferenceAPI
    catalogs: list[AttpCatalog]

    _tools: ToolsManager | None

    def __init__(
        self,
        agt_token: str,
        organization_id: int,
        *,
        connection_url: str | None = None,
        reconnect: bool = False,
        max_retries: int = 20,
        limits: Limits | None = None,
        logger: Logger | None = None,
        verbose: bool = False
    ):
        self.__agt_token = agt_token
        self.organization_id = organization_id
        self.connection_url = connection_url or "attp://localhost:6563"
        
        self.session = None
        self.max_retries = max_retries
        self.limits = limits or Limits(max_payload_size=50000)
        self.client = AttpClientSession(self.connection_url, limits=self.limits)
        self.logger = logger or getLogger("Ascender Framework")
        self.reconnect = reconnect
        
        self.route_increment_index = 2
        
        self.responder = Subject[PyAttpMessage]()
        self.routes = []
        self.catalogs = []
        self.disposable = None
        self._client = None
        self.verbose = verbose
        
        self._tools = None
        
        if self.verbose:
            init_logging()
    
    async def connect(self):
        # Open the connection
        client = await self.client.connect(self.max_retries)
        self._client = client
        
        if not client.session:
            raise ConnectionError("Failed to connect to ATTP server after 10 attempts!")
        
        self.session = SessionDriver(
            client.session, 
            agt_token=self.__agt_token, 
            organization_id=self.organization_id,
            # route_mappings=self.routes,
            factory=self.client,
            on_reconnect=self._reconnect if self.reconnect else None,
            logger=self.logger or getLogger("Ascender Framework")
        )
        asyncio.create_task(self.session.start_listener())
        # Send an authentication frame as soon as connection estabilishes with agenthub
        self.add_event_handler("tools:call", "message", self._tool_callback)
        self.add_event_handler("catalogs:tools:list", "message", self._list_tools)
        
        await self.session.authenticate(self.routes)
        asyncio.create_task(self.session.listen(self.responder))
        
        self.router = AttpRouter(self.responder, self.session)
        self.inference = AttpInferenceAPI(self.router)
        self.chats = AttpChats(self.router)
        self.agents = AttpAgents(self.router)
        
        self.disposable = self.responder.pipe(
            ops.subscribe_on(AsyncIOScheduler(asyncio.get_event_loop())),
        ).subscribe(
            on_next=lambda item: trigger_callable(self._handle_incoming, (item,)),
            on_error=lambda e: self.logger.error(f"Error in responder stream: {e}"),
        )
    
    async def _reconnect(self):
        self.logger.info("Attempting to reconnect to ATTP server...")
        await self.connect()

    async def close(self):
        if self.session:
            self.session.on_reconnect = None
            
            if self.disposable:
                self.disposable.dispose()
            
            await self.session.close()
            
            self.session = None
            self.is_connected = False

    @property
    def tools(self):
        if not self._tools:
            self._tools = ToolsManager(self.router)
        
        return self._tools
    
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

        return self.catalogs[-1] # Return the newly added catalog

    async def close_catalog(self, catalog: AttpCatalog):
        catalog.detach_all_tools()
        self.catalogs.remove(catalog)

    async def _tool_callback(self, message: PyAttpMessage):
        if not self.session:
            raise DeadSessionError(self.organization_id)
        
        if not message.correlation_id:
            await self.session.send_error(IErr(
                detail={"message": "Correlation ID was missing in the message.", "code": "MissingCorrelationId"},
            ), route=message.route_id)
            return
        
        print("TOOL CALLBACK MESSAGE:", message.payload)
        try:
            envelope = envelopizer.envelopize(message)
        except ValueError as e:
            await self.session.send_error(IErr(
                detail={"message": str(e), "code": "InvalidPayload"},
            ), correlation_id=message.correlation_id, route=message.route_id)
            return

        catalog = next((c for c in self.catalogs if c.catalog_name == envelope.catalog), None)
        if not catalog:
            await self.session.send_error(IErr(
                detail={"message": f"Catalog with name {envelope.catalog} not found.", "code": "NotFoundError"},
            ), route=message.route_id, correlation_id=message.correlation_id)
            return

        
        response = await catalog.handle_callback(envelope)
        
        if isinstance(response, IErr):
            await self.session.send_error(response, route=message.route_id, correlation_id=message.correlation_id)
            return

        if not isinstance(response, FixedBaseModel) and not isinstance(response, Serializable):
            response = Serializable[Any](response)

        await self.session.respond(route=message.route_id, correlation_id=message.correlation_id, payload=response)

    async def _list_tools(self, message: PyAttpMessage):
        if not self.session:
            raise DeadSessionError(self.organization_id)
        
        if not message.payload:
            await self.session.send_error(IErr(
                detail={"message": "Payload was missing in the message.", "code": "MissingPayload"},
            ), route=message.route_id)
            return
        
        deserialized = Serializable[dict[str, Any]].mps(message.payload)
        
        if deserialized.data.get("catalog_name") is None:
            await self.session.send_error(IErr(
                detail={"message": "Catalog name was missing in the payload.", "code": "MissingCatalogName"},
            ), route=message.route_id, correlation_id=message.correlation_id)
            return
        catalog_name = deserialized.data["catalog_name"]
        tools = self.tools.get_tools(catalog_name=catalog_name)
        
        return Serializable[dict[str, Any]]({
            "tools": [tool.model_dump(mode="json") for tool in tools]
        })
    
    async def _handle_incoming(self, message: PyAttpMessage):
        if message.route_id <= 1:
            return
        
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
                ), route=message.route_id)
                return
            if isinstance(response, StreamObject):
                iterator = response.iterate()
                if not iterator:
                    return

                # Signal beginning of stream
                await self.session.respond_stream(
                    route=message.route_id,
                    correlation_id=message.correlation_id,
                    command_type=AttpCommand.STREAMBOS,
                )

                if response.is_async:
                    async for chunk in iterator:  # type: ignore
                        await self.session.respond_stream(
                            route=message.route_id,
                            correlation_id=message.correlation_id,
                            payload=chunk,
                            command_type=AttpCommand.CHUNK,
                        )
                else:
                    for chunk in iterator:  # type: ignore
                        await self.session.respond_stream(
                            route=message.route_id,
                            correlation_id=message.correlation_id,
                            payload=chunk,
                            command_type=AttpCommand.CHUNK,
                        )

                # End of stream
                await self.session.respond_stream(
                    route=message.route_id,
                    correlation_id=message.correlation_id,
                    command_type=AttpCommand.STREAMEOS,
                )
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