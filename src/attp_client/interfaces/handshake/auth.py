from typing import Annotated
from pydantic import Field
from typing_extensions import Doc
from attp_client.misc.fixed_basemodel import FixedBaseModel


class IAuth(FixedBaseModel):
    token: Annotated[str | None, Doc("Provided AGT token for authentication")] = Field(None)
    organization_id: Annotated[int, Doc("ID of organization.")]