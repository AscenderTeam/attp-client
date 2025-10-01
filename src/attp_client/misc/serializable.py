import inspect
from typing import Any, Generic, Self, TypeVar, final

import msgpack
from pydantic import TypeAdapter

from attp_client.misc.fixed_basemodel import FixedBaseModel

T = TypeVar("T")


class Serializable(Generic[T]):
    def __init__(self, data: T, enable_validation: bool = False) -> None:
        self.data = data
        self.enable_validation = enable_validation
    
        self.validate()
    
    def validate(self):
        if isinstance(self.data, FixedBaseModel) and self.enable_validation:
            self.data = self.data.model_dump(mode="json")
    
    @staticmethod
    def deserialize(obj: bytes, mp_configs: dict[str, Any] | None = None) -> Any:
        return msgpack.unpackb(obj, **(mp_configs or {}))
    
    def serialize(self, mp_configs: dict[str, Any] | None = None) -> bytes | None:
        return msgpack.packb(self.data, **(mp_configs or {}))
    
    @final
    @classmethod
    def mps(
        cls, 
        obj: bytes,
        mp_configs: dict[str, Any] | None = None
    ) -> Self:
        """
        Message Pack Serialize
        
        Deserializes and unpacks the model from the binary by utilizing Message Pack library.

        Opposite method: `mpd(...)`

        Parameters
        ----------
        obj : bytes
            Binary packed by Message Pack object.
        """
        return cls(data=cls.deserialize(obj, mp_configs=mp_configs))
    
    @final
    def mpd(self, mp_configs: dict[str, Any] | None = None) -> bytes | None:
        """
        Message Pack Dump
        
        Dumps and packs the model to the binary by utilizing Message Pack library.
        
        Opposite method: `mps(...)`
        """
        return self.serialize(mp_configs)
    
    def __setattr__(self, name: str, value: Any) -> None:
        caller = inspect.stack()[1].function
        if caller == "__init__" or caller.startswith("_"):
            super().__setattr__(name, value)
            return
        
        if name in ["data"]:
            raise TypeError(f"'Serializable' object does not support data mutation for attribute '{name}'")