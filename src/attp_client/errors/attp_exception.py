from typing import Any, Mapping

from attp_client.interfaces.error import IErr


class AttpException(Exception):
    def __init__(self, code: str = "UnknownError", *, detail: Mapping[str, Any]) -> None:
        self.code = code
        self.detail = detail
    
    def to_ierr(self):
        return IErr(detail={"code": self.code, **self.detail})
    
    @staticmethod
    def from_ierr(err: IErr, **kwargs):
        code = err.detail.pop("code", "UnknownError")
        
        return AttpException(code=code, detail={**err.detail, **kwargs})