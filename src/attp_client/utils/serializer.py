from typing import Any

import msgpack
from pydantic import TypeAdapter
from attp_client.misc.fixed_basemodel import FixedBaseModel


def serialize(data: bytes | None, model: type[FixedBaseModel] | Any) -> FixedBaseModel | None:
    if not data:
        return None
    
    if issubclass(model, FixedBaseModel):
        return model.mps(data)
    
    return TypeAdapter(model).validate_python(msgpack.unpackb(data))


def deserialize(data: FixedBaseModel | Any | None) -> bytes | None:
    if data is None:
        return None
    
    if isinstance(data, FixedBaseModel):
        return data.mpd()
    
    return msgpack.packb(data)