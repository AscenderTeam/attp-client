from typing import Any, Self

import msgpack
from pydantic import BaseModel


class FixedBaseModel(BaseModel):
    @classmethod
    def serialize(cls, entity, **kwargs):
        serialized_data = {
            key: value
            for key, value in entity.__dict__.items()
            if not callable(value) and not key.startswith('_')
        }

        for key, value in kwargs.items():
            serialized_data[key] = value

        # noinspection PyArgumentList
        pydantic_instance = cls(**serialized_data)

        return pydantic_instance

    @classmethod
    def s(cls, entity, **kwargs) -> Self:
        return cls.serialize(entity, **kwargs)

    @classmethod
    def mps(
        cls, 
        obj: bytes,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: Any | None = None,
        by_alias: bool | None = None,
        by_name: bool | None = None,
        mp_configs: dict[str, Any] | None = None
    ):
        """
        Message Pack Serialize
        
        Serializes and unpacks the model from the binary by utilizing Message Pack library.

        Opposite method: `mpd(...)`

        Parameters
        ----------
        obj : bytes
            Binary packed by Message Pack object.
        """
        obj = msgpack.unpackb(obj, **(mp_configs or {}))
        
        return cls.model_validate(obj, strict=strict, from_attributes=from_attributes, context=context, by_alias=by_alias, by_name=by_name)
    
    def mpd(self, mp_configs: dict[str, Any] | None = None, **kwargs) -> bytes | None:
        """
        Message Pack Dump
        
        Dumps and packs the model to the binary by utilizing Message Pack library.
        
        Opposite method: `mps(...)`
        """
        return msgpack.packb(self.model_dump(mode="json", **kwargs), **(mp_configs or {}))