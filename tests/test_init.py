"""Setup, unload, devices and the config flow."""

from __future__ import annotations

from typing import Any, cast

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.reeftank import get_data
from custom_components.reeftank.compat import find_device, vol
from custom_components.reeftank.const import DOMAIN


async def test_setup_and_reload(
    hass: HomeAssistant, entry: MockConfigEntry, saved: dict[str, Any]
) -> None:
    assert get_data(hass) is entry.runtime_data
    assert entry.runtime_data.images_root.is_dir()
    assert entry.runtime_data.user_catalog_root.is_dir()

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.store.get("a1b2") is not None
    assert hass.states.get("sensor.reefer_425_fish") is not None

    assert await hass.config_entries.async_unload(entry.entry_id)
    with pytest.raises(vol.Invalid):
        get_data(hass)


async def test_device_follows_document(
    hass: HomeAssistant, entry: MockConfigEntry, saved: dict[str, Any]
) -> None:
    dev_reg = dr.async_get(hass)
    device = find_device(dev_reg, (DOMAIN, "a1b2"))
    assert device is not None and device.name == "Reefer 425"
    assert device.manufacturer == "ReefTank"

    doc = entry.runtime_data.store.get("a1b2")
    assert doc is not None
    doc["name"] = "Big reef"
    await entry.runtime_data.async_save(doc)
    device = find_device(dev_reg, (DOMAIN, "a1b2"))
    assert device is not None and device.name == "Big reef"

    assert await entry.runtime_data.async_delete("a1b2") is True
    assert find_device(dev_reg, (DOMAIN, "a1b2")) is None
    assert await entry.runtime_data.async_delete("a1b2") is False


async def test_remove_device_from_ui(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    saved: dict[str, Any],
    hass_ws_client: Any,
) -> None:
    assert await async_setup_component(hass, "config", {})
    dev_reg = dr.async_get(hass)
    device = find_device(dev_reg, (DOMAIN, "a1b2"))
    assert device is not None
    ws = await hass_ws_client(hass)
    await ws.send_json_auto_id(
        {
            "type": "config/device_registry/remove_config_entry",
            "config_entry_id": entry.entry_id,
            "device_id": device.id,
        }
    )
    msg = await ws.receive_json()
    assert msg["success"], msg
    assert entry.runtime_data.store.get("a1b2") is None
    assert dev_reg.async_get(device.id) is None


async def test_config_flow(hass: HomeAssistant) -> None:
    result: dict[str, Any] = cast(
        dict[str, Any],
        await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        ),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert await async_setup_component(hass, "http", {})
    result = cast(
        dict[str, Any],
        await hass.config_entries.flow.async_configure(result["flow_id"], {}),
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "ReefTank"

    result = cast(
        dict[str, Any],
        await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        ),
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"
