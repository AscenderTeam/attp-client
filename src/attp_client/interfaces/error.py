from typing import Any
from misc.fixed_basemodel import FixedBaseModel


class IErr(FixedBaseModel):
    detail: dict[str, Any]