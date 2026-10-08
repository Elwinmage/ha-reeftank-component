"""Inventory sensors, feeding counter and feeding event."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from conftest import sample_document, state_of
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant, State
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    mock_restore_cache,
)


async def test_inventory_sensors(
    hass: HomeAssistant, entry: MockConfigEntry, saved: dict[str, Any]
) -> None:
    fish = state_of(hass, "sensor.reefer_425_fish")
    assert fish.state == "8"
    assert fish.attributes["species"] == {"chromis_viridis": 7, "mandarin": 1}
    assert fish.attributes["species_count"] == 2
    assert state_of(hass, "sensor.reefer_425_corals").state == "1"

    doc = entry.runtime_data.store.get("a1b2")
    assert doc is not None
    doc["waters"]["main"]["livestock"][0]["count"] = 9
    await entry.runtime_data.async_save(doc)
    await hass.async_block_till_done()
    assert state_of(hass, "sensor.reefer_425_fish").state == "10"


async def test_feeding_event_and_counter(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    saved: dict[str, Any],
    freezer: FrozenDateTimeFactory,
) -> None:
    assert state_of(hass, "event.reefer_425_feeding").state == "unknown"
    assert state_of(hass, "sensor.reefer_425_feedings_today").state == "0"

    entry.runtime_data.feeding.async_feed("a1b2", "feeder", "f1")
    await hass.async_block_till_done()
    event = state_of(hass, "event.reefer_425_feeding")
    assert event.attributes["event_type"] == "feeder"
    assert event.attributes["source"] == "f1"
    counter = state_of(hass, "sensor.reefer_425_feedings_today")
    assert counter.state == "1"
    assert counter.attributes["day"] == dt_util.now().date().isoformat()

    # Next day, before the midnight tick reached the entity
    freezer.tick(24 * 3600)
    entry.runtime_data.feeding.async_feed("a1b2")
    await hass.async_block_till_done()
    assert state_of(hass, "sensor.reefer_425_feedings_today").state == "1"

    # Midnight reset
    now = dt_util.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )
    freezer.move_to(midnight)
    async_fire_time_changed(hass, midnight)
    await hass.async_block_till_done()
    assert state_of(hass, "sensor.reefer_425_feedings_today").state == "0"


async def test_counter_restored_same_day(hass: HomeAssistant) -> None:
    today = dt_util.now().date().isoformat()
    mock_restore_cache(
        hass,
        [
            State("sensor.reefer_425_feedings_today", "3", {"day": today}),
            State("sensor.other_feedings_today", "bad", {"day": today}),
            State("sensor.old_feedings_today", "5", {"day": "2000-01-01"}),
        ],
    )
    from homeassistant.setup import async_setup_component

    assert await async_setup_component(hass, "http", {})
    config_entry = MockConfigEntry(domain="reeftank", data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    data = config_entry.runtime_data
    await data.async_save({**sample_document(), "id": "a1b2"})
    await data.async_save({"id": "other", "name": "Other"})
    await data.async_save({"id": "old", "name": "Old"})
    await hass.async_block_till_done()
    assert state_of(hass, "sensor.reefer_425_feedings_today").state == "3"
    assert state_of(hass, "sensor.other_feedings_today").state == "0"
    assert state_of(hass, "sensor.old_feedings_today").state == "0"


async def test_deleted_aquarium_entities_go(
    hass: HomeAssistant, entry: MockConfigEntry, saved: dict[str, Any]
) -> None:
    await entry.runtime_data.async_delete("a1b2")
    await hass.async_block_till_done()
    assert hass.states.get("sensor.reefer_425_fish") is None
    assert hass.states.get("event.reefer_425_feeding") is None
