import asyncio
from logging import Logger, getLogger
from typing import Any
from attp_core.rs_api import AttpClientSession, Limits
from attp_core.rs_api import PyAttpMessage

from attp_client.catalog import AttpCatalog
from attp_client.inference import AttpInferenceAPI
from attp_client.interfaces.catalogs.catalog import ICatalogResponse
from attp_client.misc.serializable import Serializable
from attp_client.objects.agents import AttpAgents
from attp_client.objects.chats import AttpChats
from attp_client.core.dispatcher import AttpDispatcher
from attp_client.core.eventbus import AttpEventBus
from attp_client.core.receiver import AttpReceiver
from attp_client.core.tool_callbacks import ToolCallbacks
from attp_client.router import AttpRouter
from attp_client.session import SessionDriver
from attp_client.tools import ToolsManager

from attp_core.rs_api import init_logging


class ATTPClient:
    
    is_connected: bool
    client: AttpClientSession
    session: SessionDriver | None
    inference: AttpInferenceAPI
    catalogs: list[AttpCatalog]

    _tools: ToolsManager | None
    _tool_callbacks: ToolCallbacks | None
    eventbus: AttpEventBus | None
    receiver: AttpReceiver[tuple[SessionDriver, PyAttpMessage]] | None
    dispatcher: AttpDispatcher | None

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
        verbose: bool = False,
        verbosity_level: str = "info"
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
        
        self.catalogs = []
        self._client = None
        self.verbose = verbose
        
        self._tools = None
        self._tool_callbacks = None
        self.eventbus = None
        self.receiver = None
        self.dispatcher = None
        
        if self.verbose:
            init_logging(filter=verbosity_level)
    
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
            factory=self.client,
            on_reconnect=self._reconnect if self.reconnect else None,
            logger=self.logger or getLogger("Ascender Framework")
        )

        self.router = AttpRouter(self.session)
        self.eventbus = AttpEventBus(self.router)
        self.receiver = AttpReceiver()
        self.dispatcher = AttpDispatcher(self.eventbus, self.router)
        self.dispatcher.start(self.receiver)
        self.session.set_receiver(self.receiver)

        self._tools = ToolsManager(self.router)
        self._tool_callbacks = ToolCallbacks(
            session=self.session,
            catalogs=self.catalogs,
            tools=self._tools,
        )
        await self._tool_callbacks.register(self.eventbus)
        
        asyncio.create_task(self.session.start_listener())
        await self.session.authenticate(list(self.eventbus.routes))
        self.inference = AttpInferenceAPI(self.router)
        self.chats = AttpChats(self.router)
        self.agents = AttpAgents(self.router)
    
    async def _reconnect(self):
        self.logger.info("Attempting to reconnect to ATTP server...")
        await self.connect()

    async def close(self):
        if self.session:
            self.session.on_reconnect = None

            if self.dispatcher:
                self.dispatcher.stop()

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
