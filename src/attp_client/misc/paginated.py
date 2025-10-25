from typing import Generic, TypeVar
from pydantic import BaseModel

from .fixed_basemodel import FixedBaseModel


R = TypeVar("R", FixedBaseModel, BaseModel)


class IPaginatedResponse(FixedBaseModel, Generic[R]):
    page_size: int
    page_number: int
    items: list[R]
    total_pages: int
    total_count: int