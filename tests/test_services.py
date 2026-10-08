"""Services."""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.reeftank.const import DOMAIN, SIGNAL_FEEDING


async def test_feed(
    hass: HomeAssistant, entry: MockConfigEntry, saved: dict[str, Any]
) -> None:
    events: list[dict[str, Any]] = []
    async_dispatcher_connect(hass, SIGNAL_FEEDING.format("a1b2"), events.append)

    await hass.services.async_call(
        DOMAIN, "feed", {"aquarium": "Reefer 425", "source": "rs"}, blocking=True
    )
    await hass.async_block_till_done()
    assert events == [{"kind": "shortcut", "source": "rs"}]

    entry.runtime_data.feeding._last.clear()
    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, "a1b2")})
    assert device is not None
    await hass.services.async_call(
        DOMAIN, "feed", {"aquarium": device.id}, blocking=True
    )
    await hass.async_block_till_done()
    assert events[-1] == {"kind": "manual", "source": None}

    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(
            DOMAIN, "feed", {"aquarium": "a1b2", "source": "ghost"}, blocking=True
        )
    assert err.value.translation_key == "unknown_source"

    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(
            DOMAIN, "feed", {"aquarium": "ghost"}, blocking=True
        )
    assert err.value.translation_key == "unknown_aquarium"

    other = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("other", "x")}
    )
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "feed", {"aquarium": other.id}, blocking=True
        )


async def test_livestock(
    hass: HomeAssistant, entry: MockConfigEntry, saved: dict[str, Any]
) -> None:
    store = entry.runtime_data.store
    await hass.services.async_call(
        DOMAIN,
        "livestock_add",
        {
            "aquarium": "a1b2",
            "species": "zebrasoma",
            "count": 1,
            "size_cm": [10, 15],
            "note": "QT",
        },
        blocking=True,
    )
    line = store.get("a1b2")["waters"]["main"]["livestock"][-1]
    assert line["species"] == "zebrasoma" and line["size_cm"] == [10.0, 15.0]
    assert line["added"] is not None

    await hass.services.async_call(
        DOMAIN,
        "livestock_remove",
        {"aquarium": "a1b2", "species": "chromis_viridis", "count": 2},
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "livestock_remove",
        {"aquarium": "a1b2", "line_id": line["id"]},
        blocking=True,
    )
    lines = store.get("a1b2")["waters"]["main"]["livestock"]
    assert [ln["count"] for ln in lines if ln["species"] == "chromis_viridis"] == [5]
    assert all(ln["species"] != "zebrasoma" for ln in lines)

    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(
            DOMAIN,
            "livestock_remove",
            {"aquarium": "a1b2", "line_id": "ghost"},
            blocking=True,
        )
    assert err.value.translation_key == "unknown_line"


async def test_not_loaded(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    await hass.config_entries.async_unload(entry.entry_id)
    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(DOMAIN, "feed", {"aquarium": "x"}, blocking=True)
    assert err.value.translation_key == "not_loaded"
