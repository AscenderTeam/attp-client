from typing import Any, Mapping

from attp_client.interfaces.error import IErr


class AttpException(Exception):
    def __init__(self, code: str = "UnknownError", *, detail: Mapping[str, Any]) -> None:
        self.code = code
        self.detail = detail
    
    def to_ierr(self):
        return IErr(detail={"code": self.code, **self.detail})