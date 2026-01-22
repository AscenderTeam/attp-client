import asyncio
import traceback
from logging import Logger, getLogger
from typing import Any, Awaitable, Callable, Sequence
from uuid import uuid4


from attp_client.consts import ATTP_VERSION
from attp_client.core.receiver import AttpReceiver
from attp_client.errors.dead_session import DeadSessionError
from attp_client.errors.unauthenticated_error import UnauthenticatedError
from attp_client.interfaces.handshake.auth import IAuth
from attp_client.interfaces.error import IErr
from attp_client.interfaces.handshake.hello import IHello
from attp_client.interfaces.handshake.ready import IReady
from attp_client.interfaces.route_mappings import IRouteMapping
from attp_client.misc.fixed_basemodel import FixedBaseModel
from attp_core.rs_api import Session, PyAttpMessage, AttpCommand, AttpClientSession

from attp_client.misc.serializable import Serializable
from attp_client.types.route_mapping import AttpRouteMapping
from attp_client.utils import serializer
from attp_client.utils.route_mapper import resolve_route_by_id



class SessionDriver:
    _organization_id: int
    server_routes: Sequence[IRouteMapping] | None
    receiver: AttpReceiver[tuple["SessionDriver", PyAttpMessage]] | None
    
    def __init__(
        self, 
        session: Session, 
        agt_token: str,
        organization_id: int,
        *,
        factory: AttpClientSession,
        on_reconnect: Callable[[], Any] | None = None,
        # route_mappings: Sequence[AttpRouteMapping],
        logger: Logger = getLogger("Ascender Framework"),
    ) -> None:
        self.agt_token = agt_token
        self.on_reconnect = on_reconnect
        self.factory = factory
        self.session = session
        self._organization_id = organization_id
        self.server_routes = None
        self.logger = logger
        
        self.client_routes = []
        # self.is_authenticated = False
        self.receiver = None
        
        self.messages = asyncio.Queue[PyAttpMessage]()
        self.auth_event = asyncio.Event()
    
    @property
    def is_connected(self) -> bool:
        return bool(self.session)
    
    @property
    def session_id(self) -> str | None:
        if not self.session:
            raise DeadSessionError(self.organization_id)
        
        return self.session.session_id

    @property
    def peername(self) -> str:
        if not self.session:
            return "undefined"
        
        return self.session.peername or "undefined"
    
    @property
    def is_authenticated(self) -> bool:
        return self.auth_event.is_set()
    
    @property
    def organization_id(self) -> int:
        return self._organization_id
    
    async def send_raw(self, frame: PyAttpMessage):
        """
        Send raw message to session driver.

        Parameters
        ----------
        frame : PyAttpMessage
            Attp Frame that contains 
        """
        if not self.session:
            raise DeadSessionError(self.organization_id)
        
        return await self.session.send(frame)

    def set_receiver(self, receiver: AttpReceiver[tuple["SessionDriver", PyAttpMessage]] | None) -> None:
        self.receiver = receiver
    
    async def send_message(
        self,
        route: str | int,
        data: FixedBaseModel | Serializable | None,
        *,
        correlation_id: bytes | None = None
    ) -> bytes:
        """
        Sends an ATTPMessage to the client.

        Parameters
        ----------
        route : str | int
            String pattern of the route if str passed, or int ID of route.
        data : FixedBaseModel | Serializable | None
            A serializable data that will be sent.
        correlation_id : bytes | None, optional
            Optional correlation ID to use for the request.
        
        Returns
        -------
        bytes
            Correlation ID used for mapping the response.
        """
        if not self.session:
            raise DeadSessionError(self.organization_id)
        
        if not self.server_routes:
            raise UnauthenticatedError(f"Cannot send an ATTP message with acknowledgement to unauthenticated (route_mapping={route})")
        
        if correlation_id is None:
            correlation_id = uuid4().bytes
        relevant_route = route
        
        if isinstance(route, str):
            relevant_route = resolve_route_by_id("message", route, self.server_routes).route_id
        
        # print("RELEVANT ROUTE", relevant_route)
        
        frame = PyAttpMessage(int(relevant_route), AttpCommand.CALL, correlation_id=correlation_id, payload=data.mpd() if data is not None else None, version=ATTP_VERSION)
        # print(frame.payload)
        await self.send_raw(frame)
        
        return correlation_id
    
    
    async def emit_message(self, route: str | int, data: FixedBaseModel | Serializable | None) -> None:
        """
        Emits an ATTPMessage to the client.
        It forms the EMIT frame instead of CALL, which doesn't require receiver to respond to it.

        Parameters
        ----------
        route : str | int
            String pattern of the route if str passed, or int ID of route.
        data : FixedBaseModel | Serializable | None
            A serializable data that will be sent.
        """
        if not self.server_routes:
            raise UnauthenticatedError(f"Cannot send an ATTP message with acknowledgement to unauthenticated (route_mapping={route})")
        
        relevant_route = route
        
        if isinstance(route, str):
            relevant_route = resolve_route_by_id("event", route, self.server_routes).route_id
        
        frame = PyAttpMessage(int(relevant_route), AttpCommand.EMIT, correlation_id=None, payload=data.mpd() if data is not None else None, version=ATTP_VERSION)
        await self.send_raw(frame)
    
    async def authenticate(self, route_mappings: Sequence[AttpRouteMapping] | None) -> None:
        """
        Send AUTH frame to attp server (AgentHub).
        Version should be b'01' in bytes.

        Parameters
        ----------
        version : bytes
            Version of ATTP protocol (to validate on Rust side). It's 01, which correlated to '0.1'

        Returns
        -------
        tuple[str, int]
            (session_id, organization_id) - client sends organization_id while session ID is generated by Rust.
        """
        if route_mappings:
            self.client_routes.extend([IRouteMapping.from_route_mapper(mapper) for mapper in route_mappings])
        
        frame = PyAttpMessage(
            route_id=0, 
            command_type=AttpCommand.AUTH, 
            correlation_id=None,
            payload=IAuth(
                token=self.agt_token, 
                organization_id=self.organization_id
            ).mpd(),
            version=ATTP_VERSION
        )
        await self.send_raw(frame)
        
        await asyncio.wait_for(self.auth_event.wait(), 10)

    async def send_error(self, err: IErr, correlation_id: bytes | None = None, route: str | int = 0) -> None:
        """
        Send an error to the session peer.
        Can be two types, non correlated to ack and correlated to ack.
        
        When correlated to ack, the `correlation_id` as a response to acknowledgement is required to specify.

        Parameters
        ----------
        err : IErr
            Error details.
        correlation_id : bytes | None, optional
            For correlated to ack, ID of the correlation as a response error, by default None (non-correlated)
        route : str | int, optional
            For correlated to ack, not required and not allowed to specify route, but for non-correlated it's optional, by default 0
        """
        relevant_route = route
        
        if not self.server_routes:
            raise UnauthenticatedError(f"Cannot send an ATTP message with acknowledgement to unauthenticated (route_mapping={route})")
        
        
        if isinstance(route, str):
            relevant_route = resolve_route_by_id("err", route, self.server_routes).route_id
        
        await self.send_raw(
            PyAttpMessage(
                route_id=int(relevant_route),
                command_type=AttpCommand.ERR,
                correlation_id=correlation_id,
                payload=err.mpd(),
                version=ATTP_VERSION
            )
        )
    
    async def respond(self, route: int | str, correlation_id: bytes, payload: FixedBaseModel | Serializable | Any | None = None):
        """
        For responding to `AttpCommand.CALL`. Used only for correlated requests.
        It sends response (acknowledgement) message signed as `AttpCommand.ACK` to the request.

        Parameters
        ----------
        correlation_id : bytes
            Correlation ID to which response is being sent.
        payload : FixedBaseModel | Serializable | None, optional
            Response payload, the data that will be sent, by default None
        """
        relevant_route = route

        if not self.server_routes:
            raise UnauthenticatedError(f"Cannot send an ATTP message with acknowledgement to unauthenticated (route_mapping={route})")
        
        if isinstance(route, str):
            relevant_route = resolve_route_by_id("message", route, self.server_routes).route_id

        frame = PyAttpMessage(
            route_id=int(relevant_route),
            command_type=AttpCommand.ACK,
            correlation_id=correlation_id,
            payload=serializer.deserialize(payload),
            version=ATTP_VERSION
        )
        
        await self.send_raw(frame)

    async def respond_stream(
        self,
        route: int | str,
        correlation_id: bytes,
        *,
        payload: FixedBaseModel | Serializable | Any | None = None,
        command_type: AttpCommand,
    ):
        """
        Send a streaming response frame (STREAMBOS/CHUNK/STREAMEOS) for a correlated request.
        """
        relevant_route = route

        if not self.server_routes:
            raise UnauthenticatedError(
                f"Cannot send an ATTP stream message to unauthenticated session (route_mapping={route})"
            )

        if isinstance(route, str):
            relevant_route = resolve_route_by_id("message", route, self.server_routes).route_id

        frame = PyAttpMessage(
            route_id=int(relevant_route),
            command_type=command_type,
            correlation_id=correlation_id,
            payload=serializer.deserialize(payload),
            version=ATTP_VERSION,
        )

        await self.send_raw(frame)

    async def listen(self, on_message: Callable[[PyAttpMessage], Awaitable[None]]) -> None:
        """
        Start a background read-loop task that:
          - Routes CALL, EMIT -> `events` (apply backpressure with await put)
          - Routes ACK, ERR   -> response handler
        Must:
          - batch across the FFI boundary
          - enforce correlation rules:
              * CALL must include Correlation-Id
              * ACK/ERR must include Correlation-Id
          - propagate terminal errors by finishing the Task with an exception
          - stop cleanly on orderly close
        """
        while self.is_authenticated:
            message = await self.messages.get()
            await on_message(message)

    async def close(self):
        """
        Closes the connection from server-side between the client.
        """
        await self.send_raw(PyAttpMessage(
            route_id=0,
            command_type=AttpCommand.DISCONNECT,
            correlation_id=None,
            payload=None,
            version=ATTP_VERSION
        ))
        self.session.stop_listener()
        self.session.disconnect()
    
    async def handle_ready(self, frame: IReady):
        self.server_routes = frame.server_routes
        
        # print(frame.server_routes)
        
        data = PyAttpMessage(
            route_id=0,
            command_type=AttpCommand.READY,
            correlation_id=None,
            payload=IHello(proto="attp", ver="0.1", caps=[], mapping=self.client_routes).mpd(),
            version=b"01"
        )
        await self.send_raw(data)
        self.auth_event.set()
    
    async def _on_event(self, events: list[PyAttpMessage]) -> None:
        try:
            try:
                session_id = self.session_id
            except Exception:
                session_id = "unknown"

            self.logger.debug(f"[cyan]ATTP[/] ┆ Received a new message from session {session_id} ")
            # assert self.session
            
            for event in events:
                try:
                    if event.route_id == 0 and event.command_type == AttpCommand.READY:
                        if not event.payload:
                            continue
                        
                        try:
                            await self.handle_ready(IReady.mps(event.payload))
                        except Exception:
                            traceback.print_exc()
                            self.logger.exception("[cyan]ATTP[/] ┆ Failed to handle READY frame.")
                            await self.close()
                            break
                        continue
                    
                    if event.command_type == AttpCommand.DISCONNECT:
                        self.messages.put_nowait(event)
                        self.logger.info(f"[cyan]ATTP[/] ┆ Session {self.session_id} disconnected by the server.")
                        await self.close()
                        
                        if self.on_reconnect:
                            self.logger.info(f"[cyan]ATTP[/] ┆ Attempting to reconnect session for organization {self.organization_id}...")
                            try:
                                await self.on_reconnect()
                                self.logger.info(f"[cyan]ATTP[/] ┆ Successfully reconnected session for organization {self.organization_id}.")
                            except Exception:
                                traceback.print_exc()
                                self.logger.exception(f"[cyan]ATTP[/] ┆ Failed to reconnect session for organization {self.organization_id}.")
                    else:
                        if self.is_authenticated:
                            self.logger.debug("[cyan]ATTP[/] ┆ Handing incoming message to a route handler.")
                            if self.receiver:
                                self.receiver.on_next((self, event))
                            else:
                                self.messages.put_nowait(event)
                except Exception:
                    traceback.print_exc()
                    self.logger.exception(
                        "[cyan]ATTP[/] ┆ Failed to process incoming frame "
                        f"(route_id={event.route_id}, command_type={event.command_type})."
                    )
        except Exception:
            traceback.print_exc()
            self.logger.exception("[cyan]ATTP[/] ┆ Unhandled error in _on_event handler.")

    async def start_listener(self):
        if not self.session:
            raise DeadSessionError(self.organization_id)
        self.session.add_event_handler(self._on_event)
        
        await asyncio.gather(
            self.session.start_handler(),
            self.session.start_listener()
        )