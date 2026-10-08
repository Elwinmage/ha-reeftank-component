"""WebSocket API."""

from __future__ import annotations

from typing import Any

from conftest import sample_document
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_list_get_catalog(
    hass: HomeAssistant, saved: dict[str, Any], hass_ws_client: Any
) -> None:
    ws = await hass_ws_client(hass)
    await ws.send_json_auto_id({"type": "reeftank/aquarium/list"})
    msg = await ws.receive_json()
    assert msg["success"]
    assert msg["result"] == [
        {
            "id": "a1b2",
            "name": "Reefer 425",
            "revision": 1,
            "preset": None,
            "cloud": None,
            "render_level": "full",
            "views": 2,
        }
    ]

    await ws.send_json_auto_id({"type": "reeftank/aquarium/get", "aquarium_id": "a1b2"})
    msg = await ws.receive_json()
    assert msg["result"]["document"]["name"] == "Reefer 425"
    assert msg["result"]["images_url"] == "/reeftank/images"
    entities = msg["result"]["entities"]
    assert entities["feeding"] == "event.reefer_425_feeding"
    assert entities["fish"] == "sensor.reefer_425_fish"

    await ws.send_json_auto_id(
        {"type": "reeftank/aquarium/get", "aquarium_id": "ghost"}
    )
    msg = await ws.receive_json()
    assert msg["error"]["code"] == "not_found"

    await ws.send_json_auto_id({"type": "reeftank/catalog"})
    msg = await ws.receive_json()
    assert [e["id"] for e in msg["result"]["fish"]] == ["demo_damselfish"]
    assert msg["result"]["fish"][0]["atlas"]["1x"].startswith(
        "/reeftank/catalog/bundled/fish/"
    )


async def test_subscribe(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    saved: dict[str, Any],
    hass_ws_client: Any,
) -> None:
    ws = await hass_ws_client(hass)
    await ws.send_json_auto_id(
        {"type": "reeftank/aquarium/subscribe", "aquarium_id": "a1b2"}
    )
    msg = await ws.receive_json()
    assert msg["success"]
    event = await ws.receive_json()
    assert event["event"]["document"]["revision"] == 1

    doc = entry.runtime_data.store.get("a1b2")
    doc["name"] = "Renamed"
    await entry.runtime_data.async_save(doc)
    event = await ws.receive_json()
    assert event["event"]["document"]["name"] == "Renamed"

    await entry.runtime_data.async_delete("a1b2")
    event = await ws.receive_json()
    assert event["event"] == {"deleted": True}

    await ws.send_json_auto_id(
        {"type": "reeftank/aquarium/subscribe", "aquarium_id": "ghost"}
    )
    msg = await ws.receive_json()
    assert msg["error"]["code"] == "not_found"


async def test_subscription_after_unload(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    saved: dict[str, Any],
    hass_ws_client: Any,
) -> None:
    """A change arriving while the integration is unloaded is not forwarded."""
    ws = await hass_ws_client(hass)
    await ws.send_json_auto_id(
        {"type": "reeftank/aquarium/subscribe", "aquarium_id": "a1b2"}
    )
    await ws.receive_json()
    await ws.receive_json()
    data = entry.runtime_data
    await hass.config_entries.async_unload(entry.entry_id)
    from homeassistant.helpers.dispatcher import async_dispatcher_send

    from custom_components.reeftank.const import SIGNAL_AQUARIUM_UPDATED

    async_dispatcher_send(
        hass, SIGNAL_AQUARIUM_UPDATED.format("a1b2"), data.store.get("a1b2")
    )
    await hass.async_block_till_done()
    await ws.send_json_auto_id({"type": "reeftank/aquarium/list"})
    msg = await ws.receive_json()
    assert msg["error"]["code"] == "not_loaded"


async def test_save_and_delete(
    hass: HomeAssistant, entry: MockConfigEntry, hass_ws_client: Any
) -> None:
    ws = await hass_ws_client(hass)
    await ws.send_json_auto_id(
        {"type": "reeftank/aquarium/save", "document": sample_document()}
    )
    msg = await ws.receive_json()
    assert msg["success"], msg
    doc = msg["result"]["document"]
    assert doc["revision"] == 1

    await ws.send_json_auto_id(
        {"type": "reeftank/aquarium/save", "document": doc, "expected_revision": 1}
    )
    msg = await ws.receive_json()
    assert msg["result"]["document"]["revision"] == 2

    await ws.send_json_auto_id(
        {"type": "reeftank/aquarium/save", "document": doc, "expected_revision": 1}
    )
    msg = await ws.receive_json()
    assert msg["error"]["code"] == "conflict"

    await ws.send_json_auto_id(
        {"type": "reeftank/aquarium/save", "document": {"name": ""}}
    )
    msg = await ws.receive_json()
    assert msg["error"]["code"] == "invalid_format"

    await ws.send_json_auto_id(
        {"type": "reeftank/aquarium/delete", "aquarium_id": doc["id"]}
    )
    msg = await ws.receive_json()
    assert msg["success"]
    await ws.send_json_auto_id(
        {"type": "reeftank/aquarium/delete", "aquarium_id": doc["id"]}
    )
    msg = await ws.receive_json()
    assert msg["error"]["code"] == "not_found"


async def test_writes_need_admin(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    hass_ws_client: Any,
    hass_read_only_access_token: str,
) -> None:
    ws = await hass_ws_client(hass, hass_read_only_access_token)
    await ws.send_json_auto_id(
        {"type": "reeftank/aquarium/save", "document": sample_document()}
    )
    msg = await ws.receive_json()
    assert msg["error"]["code"] == "unauthorized"


async def test_not_loaded(
    hass: HomeAssistant, entry: MockConfigEntry, hass_ws_client: Any
) -> None:
    await hass.config_entries.async_unload(entry.entry_id)
    ws = await hass_ws_client(hass)
    for payload in (
        {"type": "reeftank/aquarium/list"},
        {"type": "reeftank/aquarium/get", "aquarium_id": "a"},
        {"type": "reeftank/aquarium/subscribe", "aquarium_id": "a"},
        {"type": "reeftank/aquarium/save", "document": {"name": "x"}},
        {"type": "reeftank/aquarium/delete", "aquarium_id": "a"},
        {"type": "reeftank/catalog"},
    ):
        await ws.send_json_auto_id(payload)
        msg = await ws.receive_json()
        assert msg["error"]["code"] == "not_loaded", payload
