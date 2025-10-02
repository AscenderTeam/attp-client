from typing import Annotated, Any, Mapping
from pydantic import Field
from typing_extensions import Doc
from attp_client.misc.fixed_basemodel import FixedBaseModel


class IEnvelope(FixedBaseModel):
    """Uniform tool output"""
    type: Annotated[str, Doc("Envelop discriminator; For tools only 'tool-call'")] = Field("tool-call")
    catalog: Annotated[str, Doc("Tool catalog name where tool is registered and being called from")]
    tool_id: Annotated[str, Doc("Tool ID being called")]
    metadata: Annotated[Mapping[str, Any], Doc("AgentHub/trace metadata")] = Field(default_factory=dict)
    data: Annotated[Mapping[str, Any], Doc("Tool output JSON matching provided tool arg schema")]