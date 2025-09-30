import inspect
from typing import Any, Generic, Self, TypeVar

import msgpack

T = TypeVar("T")


class Serializable(Generic[T]):
    def __init__(self, data: T) -> None:
        self.data = data
    
    @staticmethod
    def serialize(obj: bytes, mp_configs: dict[str, Any] | None = None):
        return msgpack.unpackb(obj, **(mp_configs or {}))
    
    def deserialize(self, mp_configs: dict[str, Any] | None = None):
        msgpack.packb(self.data, **(mp_configs or {}))
    
    @classmethod
    def mps(
        cls, 
        obj: bytes,
        mp_configs: dict[str, Any] | None = None
    ) -> Self:
        """
        Message Pack Serialize
        
        Serializes and unpacks the model from the binary by utilizing Message Pack library.

        Opposite method: `mpd(...)`

        Parameters
        ----------
        obj : bytes
            Binary packed by Message Pack object.
        """
        return cls(data=cls.serialize(obj, mp_configs=mp_configs))
    
    def mpd(self, mp_configs: dict[str, Any] | None = None) -> bytes | None:
        """
        Message Pack Dump
        
        Dumps and packs the model to the binary by utilizing Message Pack library.
        
        Opposite method: `mps(...)`
        """
        return self.deserialize(mp_configs)
    
    def __setattr__(self, name: str, value: Any) -> None:
        caller = inspect.stack()[1].function
        if caller == "__init__" or caller.startswith("_"):
            super().__setattr__(name, value)
            return
        
        if name in ["data"]:
            raise TypeError(f"'Serializable' object does not support data mutation for attribute '{name}'")