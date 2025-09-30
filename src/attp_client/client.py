import asyncio
from logging import Logger, getLogger
from typing import Any, Callable, Literal
from attp_core.rs_api import AttpClientSession, Limits
from reactivex import Subject
from attp_core.rs_api import PyAttpMessage

from attp_client.router import AttpRouter
from attp_client.session import SessionDriver
from attp_client.types.route_mapping import AttpRouteMapping, RouteType

class ATTPClient:
    
    is_connected: bool
    client: AttpClientSession
    session: SessionDriver | None
    routes: list[AttpRouteMapping]
    
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
        self.connection_url = connection_url or "attp://localhost"
        
        self.client = AttpClientSession(self.connection_url)
        self.session = None
        self.max_retries = max_retries
        self.limits = limits or Limits(max_payload_size=2000)
        self.logger = logger
        
        self.route_increment_index = 2
        
        self.responder = Subject[PyAttpMessage]()
        self.routes = []
    
    async def connect(self):
        # Open the connection
        client = await self.client.connect(self.max_retries, self.limits)
        
        if not client.session:
            raise ConnectionError("Failed to connect to ATTP server after 10 attempts!")
        
        self.session = SessionDriver(
            client.session, 
            agt_token=self.__agt_token, 
            organization_id=self.organization_id,
            route_mappings=self.routes,
            logger=self.logger or getLogger("Ascender Framework")
        )
        # Send an authentication frame as soon as connection estabilishes with agenthub
        await self.session.authenticate(self.routes)
        asyncio.create_task(self.session.listen(self.responder))
        
        self.router = AttpRouter(self.responder, self.session)

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