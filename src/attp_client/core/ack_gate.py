import asyncio

from attp_core.rs_api import PyAttpMessage, AttpCommand

from attp_client.errors.attp_exception import AttpException
from attp_client.interfaces.error import IErr


class StatefulAckGate:
    def __init__(self) -> None:
        self.pendings: dict[bytes, asyncio.Queue] = {}
        self.pending_lock = asyncio.Lock()
    
    async def request_ack(self, correlation_id: bytes):
        async with self.pending_lock:
            queue = self.pendings.get(correlation_id)
            if queue is None:
                queue = asyncio.Queue()
                self.pendings[correlation_id] = queue
        
        return queue

    async def feed(self, message: PyAttpMessage) -> None:
        if not message.correlation_id:
            return

        async with self.pending_lock:
            queue = self.pendings.get(message.correlation_id)
            if queue is None:
                return

        queue.put_nowait(message)
    
    async def wait_for_ack(
        self, 
        correlation_id: bytes, 
        timeout: float,
        *, queue: asyncio.Queue[PyAttpMessage] | None = None
    ):
        if not queue:
            queue = self.pendings.get(correlation_id) or await self.request_ack(correlation_id)
        
        while True:
            message = await asyncio.wait_for(queue.get(), timeout=timeout)
            
            if message.command_type == AttpCommand.ERR:
                raise AttpException.from_ierr(
                    err=IErr.mps(message.payload) if message.payload else IErr(detail={"code": "ErrorWithoutPayload"}),
                    correlation_id=correlation_id
                )
            if message.command_type == AttpCommand.DEFER:
                continue
            
            if message.command_type == AttpCommand.ACK:
                return message
    
    async def stream_ack(
        self,
        correlation_id: bytes,
        timeout: float,
        *, queue: asyncio.Queue[PyAttpMessage] | None = None
    ):
        if not queue:
            queue = self.pendings.get(correlation_id) or await self.request_ack(correlation_id)

        while True:
            message = await asyncio.wait_for(queue.get(), timeout=timeout)
            
            if message.command_type == AttpCommand.ERR:
                raise AttpException.from_ierr(
                    err=IErr.mps(message.payload) if message.payload else IErr(detail={"code": "ErrorWithoutPayload"}),
                    correlation_id=correlation_id
                )
            if message.command_type == AttpCommand.STREAMBOS:
                continue
            
            if message.command_type == AttpCommand.CHUNK:
                yield message
            
            if message.command_type == AttpCommand.STREAMEOS:
                return
        
    async def complete_ack(self, correlation_id: bytes):
        """Call when response is returned and theres no need for the corr_id to be hanging on pending"""
        async with self.pending_lock:
            self.pendings.pop(correlation_id, None)
