from typing import Any
from attp_client.misc.fixed_basemodel import FixedBaseModel


class IErr(FixedBaseModel):
    detail: dict[str, Any]