from attp_client.misc.fixed_basemodel import FixedBaseModel


class ToolV2(FixedBaseModel):
    name: str
    db_id: int | None = None