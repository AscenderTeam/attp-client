import asyncio
import traceback
from attp_client.core.eventbus import AttpEventBus
from attp_client.core.receiver import AttpReceiver
from attp_client.interfaces.error import IErr
from attp_client.router import AttpRouter
from attp_client.session import SessionDriver

from attp_core.rs_api import PyAttpMessage, AttpCommand


class AttpDispatcher:
    def __init__(self, eventbus: AttpEventBus, router: AttpRouter) -> None:
        self.eventbus = eventbus
        self.router = router
        self._task: asyncio.Task | None = None
        
    def start(self, receiver: AttpReceiver[tuple[SessionDriver, PyAttpMessage]]) -> None:
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._run(receiver))

    def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()

    async def _run(self, receiver: AttpReceiver[tuple[SessionDriver, PyAttpMessage]]) -> None:
        while True:
            session, msg = await receiver.get()
            try:
                if msg.command_type in (
                    AttpCommand.ACK,
                    AttpCommand.ERR,
                    AttpCommand.DEFER,
                    AttpCommand.STREAMBOS,
                    AttpCommand.CHUNK,
                    AttpCommand.STREAMEOS,
                ):
                    await self.router.handle_response(msg)
                else:
                    await self.eventbus.emit(session, msg)
            except Exception:
                traceback.print_exc()
                if msg.command_type == AttpCommand.CALL and msg.correlation_id:
                    await session.send_error(
                        IErr(detail={"code": "InternalDispatchError", "message": "Dispatcher failed to process frame."}),
                        correlation_id=msg.correlation_id,
                        route=msg.route_id
                    )
            finally:
                receiver.task_done()
