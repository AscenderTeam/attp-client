from uuid import UUID
from attp_client.misc.fixed_basemodel import FixedBaseModel


class ITool(FixedBaseModel):
    """Tool interface definition"""
    id: UUID | str
    name: str
    description: str | None = None
    schema_id: str | None = None
    schema: dict | None = None
    return_direct: bool = False
    schema_ver: str = "1.0"
    timeout_ms: float = 20000
    idempotent: bool = False
    config: dict | None = None
    
    catalog: str