"""WebSocket API used by the card and its scene editor."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.components.websocket_api import async_register_command
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.components.websocket_api.decorators import (
    async_response,
    require_admin,
    websocket_command,
)
from homeassistant.components.websocket_api.messages import event_message
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (
    DOMAIN,
    SIGNAL_AQUARIUM_UPDATED,
    URL_CATALOG_BUNDLED,
    URL_CATALOG_USER,
    URL_IMAGES,
)
from .store import RevisionConflict

if TYPE_CHECKING:
    from . import ReefTankData

ERR_NOT_LOADED = "not_loaded"
ERR_NOT_FOUND = "not_found"
ERR_INVALID = "invalid_format"
ERR_CONFLICT = "conflict"


def _data(hass: HomeAssistant) -> ReefTankData | None:
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        return entry.runtime_data
    return None


@callback
def async_register_websocket(hass: HomeAssistant) -> None:
    """Register the commands (once, at integration setup)."""
    for command in (
        ws_list,
        ws_get,
        ws_subscribe,
        ws_save,
        ws_delete,
        ws_catalog,
    ):
        async_register_command(hass, command)


def _summary(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": doc["id"],
        "name": doc["name"],
        "revision": doc["revision"],
        "preset": doc.get("preset"),
        "cloud": doc.get("cloud"),
        "render_level": doc["render"]["level"],
        "views": len(doc["views"]),
    }


def _payload(data: ReefTankData, doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "document": doc,
        "entities": data.entity_ids(doc["id"]),
        "images_url": URL_IMAGES,
    }


@websocket_command({vol.Required("type"): "reeftank/aquarium/list"})
@callback
def ws_list(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """List the aquariums."""
    data = _data(hass)
    if data is None:
        connection.send_error(msg["id"], ERR_NOT_LOADED, "reeftank is not set up")
        return
    connection.send_result(msg["id"], [_summary(doc) for doc in data.store.all()])


@websocket_command(
    {
        vol.Required("type"): "reeftank/aquarium/get",
        vol.Required("aquarium_id"): str,
    }
)
@callback
def ws_get(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return one aquarium document and its entity ids."""
    data = _data(hass)
    if data is None:
        connection.send_error(msg["id"], ERR_NOT_LOADED, "reeftank is not set up")
        return
    doc = data.store.get(msg["aquarium_id"])
    if doc is None:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "unknown aquarium")
        return
    connection.send_result(msg["id"], _payload(data, doc))


@websocket_command(
    {
        vol.Required("type"): "reeftank/aquarium/subscribe",
        vol.Required("aquarium_id"): str,
    }
)
@callback
def ws_subscribe(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Send an aquarium document now and again on every change.

    Every event carries the whole document; a deleted aquarium sends
    {"deleted": true} once.
    """
    data = _data(hass)
    if data is None:
        connection.send_error(msg["id"], ERR_NOT_LOADED, "reeftank is not set up")
        return
    aquarium_id = msg["aquarium_id"]
    doc = data.store.get(aquarium_id)
    if doc is None:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "unknown aquarium")
        return

    @callback
    def _forward(new_doc: dict[str, Any] | None) -> None:
        if new_doc is None:
            connection.send_message(event_message(msg["id"], {"deleted": True}))
            return
        current = _data(hass)
        if current is not None:
            connection.send_message(
                event_message(msg["id"], _payload(current, new_doc))
            )

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(
        hass, SIGNAL_AQUARIUM_UPDATED.format(aquarium_id), _forward
    )
    connection.send_result(msg["id"])
    connection.send_message(event_message(msg["id"], _payload(data, doc)))


@websocket_command(
    {
        vol.Required("type"): "reeftank/aquarium/save",
        vol.Required("document"): dict,
        vol.Optional("expected_revision"): vol.Any(None, int),
    }
)
@require_admin
@async_response
async def ws_save(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Create or replace an aquarium document."""
    data = _data(hass)
    if data is None:
        connection.send_error(msg["id"], ERR_NOT_LOADED, "reeftank is not set up")
        return
    try:
        doc = await data.async_save(msg["document"], msg.get("expected_revision"))
    except RevisionConflict as err:
        connection.send_error(
            msg["id"],
            ERR_CONFLICT,
            f"changed elsewhere (revision {err.current['revision']})",
        )
        return
    except vol.Invalid as err:
        connection.send_error(msg["id"], ERR_INVALID, str(err))
        return
    connection.send_result(msg["id"], _payload(data, doc))


@websocket_command(
    {
        vol.Required("type"): "reeftank/aquarium/delete",
        vol.Required("aquarium_id"): str,
    }
)
@require_admin
@async_response
async def ws_delete(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Delete an aquarium with its device, entities and pictures."""
    data = _data(hass)
    if data is None:
        connection.send_error(msg["id"], ERR_NOT_LOADED, "reeftank is not set up")
        return
    if not await data.async_delete(msg["aquarium_id"]):
        connection.send_error(msg["id"], ERR_NOT_FOUND, "unknown aquarium")
        return
    connection.send_result(msg["id"])


@websocket_command({vol.Required("type"): "reeftank/catalog"})
@async_response
async def ws_catalog(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return the merged asset catalog (bundled + user)."""
    from . import BUNDLED_CATALOG
    from .catalog import load_catalog

    data = _data(hass)
    if data is None:
        connection.send_error(msg["id"], ERR_NOT_LOADED, "reeftank is not set up")
        return
    catalog = await hass.async_add_executor_job(
        load_catalog,
        BUNDLED_CATALOG,
        URL_CATALOG_BUNDLED,
        data.user_catalog_root,
        URL_CATALOG_USER,
    )
    connection.send_result(msg["id"], catalog)
