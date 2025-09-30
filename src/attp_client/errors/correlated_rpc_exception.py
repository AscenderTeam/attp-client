from typing import Any
from uuid import UUID

from attp_client.interfaces.error import IErr

class CorrelatedRPCException(Exception):
    correlation_id: UUID
    def __init__(
        self, 
        correlation_id: bytes,
        detail: dict[str, Any] | None = None,
    ):
        self.correlation_id = UUID(bytes=correlation_id)
        self.detail = detail
    
    @staticmethod
    def from_err_object(correlation_id: bytes, err: IErr):
        return CorrelatedRPCException(correlation_id, err.detail)
    
    def __str__(self) -> str:
        return f"[ATTPRPC ERR]: {self.detail}"