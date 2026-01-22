from typing import Any

from attp_core.rs_api import PyAttpMessage

from attp_client.catalog import AttpCatalog
from attp_client.interfaces.error import IErr
from attp_client.misc.fixed_basemodel import FixedBaseModel
from attp_client.misc.serializable import Serializable
from attp_client.session import SessionDriver
from attp_client.tools import ToolsManager
from attp_client.core.eventbus import AttpEventBus
from attp_client.utils import envelopizer


class ToolCallbacks:
    def __init__(
        self,
        *,
        session: SessionDriver,
        catalogs: list[AttpCatalog],
        tools: ToolsManager,
    ) -> None:
        self._session = session
        self._catalogs = catalogs
        self._tools = tools

    async def register(self, eventbus: AttpEventBus) -> None:
        await eventbus.subscribe("message", "tools:call", self.handle_tool_call)
        await eventbus.subscribe("message", "catalogs:tools:list", self.list_tools)

    async def handle_tool_call(self, message: PyAttpMessage):
        if not message.correlation_id:
            await self._session.send_error(IErr(
                detail={"message": "Correlation ID was missing in the message.", "code": "MissingCorrelationId"},
            ), route=message.route_id)
            return

        print("TOOL CALLBACK MESSAGE:", message.payload)
        try:
            envelope = envelopizer.envelopize(message)
        except ValueError as e:
            await self._session.send_error(IErr(
                detail={"message": str(e), "code": "InvalidPayload"},
            ), correlation_id=message.correlation_id, route=message.route_id)
            return

        catalog = next((c for c in self._catalogs if c.catalog_name == envelope.catalog), None)
        if not catalog:
            await self._session.send_error(IErr(
                detail={"message": f"Catalog with name {envelope.catalog} not found.", "code": "NotFoundError"},
            ), route=message.route_id, correlation_id=message.correlation_id)
            return

        response = await catalog.handle_callback(envelope)

        if isinstance(response, IErr):
            await self._session.send_error(response, route=message.route_id, correlation_id=message.correlation_id)
            return

        if not isinstance(response, FixedBaseModel) and not isinstance(response, Serializable):
            response = Serializable[Any](response)

        await self._session.respond(route=message.route_id, correlation_id=message.correlation_id, payload=response)

    async def list_tools(self, message: PyAttpMessage):
        if not message.payload:
            await self._session.send_error(IErr(
                detail={"message": "Payload was missing in the message.", "code": "MissingPayload"},
            ), route=message.route_id)
            return

        deserialized = Serializable[dict[str, Any]].mps(message.payload)

        if deserialized.data.get("catalog_name") is None:
            await self._session.send_error(IErr(
                detail={"message": "Catalog name was missing in the payload.", "code": "MissingCatalogName"},
            ), route=message.route_id, correlation_id=message.correlation_id)
            return

        catalog_name = deserialized.data["catalog_name"]
        tools = self._tools.get_tools(catalog_name=catalog_name)

        return Serializable[dict[str, Any]]({
            "tools": [tool.model_dump(mode="json") for tool in tools]
        })
