"""Feeding sources, triggers and deduplication."""

from __future__ import annotations

from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.reeftank.const import SIGNAL_FEEDING
from custom_components.reeftank.feeding import default_kind, is_trigger


@pytest.mark.parametrize(
    ("entity_id", "old", "new", "expected"),
    [
        ("sensor.feeder", "2026-01-01", "2026-01-02", True),
        ("sensor.feeder", "a", "a", False),
        ("sensor.feeder", None, "a", False),
        ("sensor.feeder", "unavailable", "a", False),
        ("sensor.feeder", "a", "unknown", False),
        ("switch.feeding", "off", "on", True),
        ("switch.feeding", "on", "off", False),
        ("button.feed", "2026-01-01T10:00", "2026-01-01T11:00", True),
    ],
)
def test_is_trigger(
    entity_id: str, old: str | None, new: str | None, expected: bool
) -> None:
    assert is_trigger(entity_id, old, new) is expected


def test_default_kind() -> None:
    assert default_kind("switch.feeding") == "shortcut"
    assert default_kind("binary_sensor.x") == "shortcut"
    assert default_kind("sensor.feeder") == "feeder"


async def test_sources_fire_feedings(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    saved: dict[str, Any],
    freezer: FrozenDateTimeFactory,
) -> None:
    events: list[dict[str, Any]] = []
    async_dispatcher_connect(hass, SIGNAL_FEEDING.format("a1b2"), events.append)

    hass.states.async_set("sensor.feeder_last_feed", "t0")
    hass.states.async_set("switch.feeding", "off")
    await hass.async_block_till_done()
    assert events == []

    hass.states.async_set("sensor.feeder_last_feed", "t1")
    await hass.async_block_till_done()
    assert events == [{"kind": "feeder", "source": "f1"}]

    # Within the dedup window: merged
    hass.states.async_set("switch.feeding", "on")
    await hass.async_block_till_done()
    assert len(events) == 1

    freezer.tick(200)
    hass.states.async_set("switch.feeding", "off")
    hass.states.async_set("switch.feeding", "on")
    await hass.async_block_till_done()
    assert events[-1] == {"kind": "shortcut", "source": "rs"}

    # Unrelated entity
    hass.states.async_set("sensor.other", "1")
    hass.states.async_set("sensor.other", "2")
    await hass.async_block_till_done()
    assert len(events) == 2


async def test_sources_follow_document(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    saved: dict[str, Any],
    freezer: FrozenDateTimeFactory,
) -> None:
    data = entry.runtime_data
    events: list[dict[str, Any]] = []
    async_dispatcher_connect(hass, SIGNAL_FEEDING.format("a1b2"), events.append)

    doc = data.store.get("a1b2")
    doc["feeding"]["sources"] = [
        {"id": "nb", "entity_id": "button.feed", "kind": "manual"}
    ]
    doc["views"]["front"]["elements"][1]["source"] = "nb"
    await data.async_save(doc)
    hass.states.async_set("sensor.feeder_last_feed", "t0")
    hass.states.async_set("sensor.feeder_last_feed", "t1")
    hass.states.async_set("button.feed", "t0")
    hass.states.async_set("button.feed", "t1")
    await hass.async_block_till_done()
    assert events == [{"kind": "manual", "source": "nb"}]

    # No source at all
    doc = data.store.get("a1b2")
    doc["feeding"]["sources"] = []
    doc["views"]["front"]["elements"][1]["source"] = None
    await data.async_save(doc)
    freezer.tick(500)
    hass.states.async_set("button.feed", "t2")
    await hass.async_block_till_done()
    assert len(events) == 1

    # Deleted aquarium: nothing left watching, feeding refused
    await data.async_delete("a1b2")
    await hass.async_block_till_done()
    assert data.feeding.async_feed("a1b2") is False


async def test_feed_normalises_kind(
    hass: HomeAssistant, entry: MockConfigEntry, saved: dict[str, Any]
) -> None:
    events: list[dict[str, Any]] = []
    async_dispatcher_connect(hass, SIGNAL_FEEDING.format("a1b2"), events.append)
    assert entry.runtime_data.feeding.async_feed("a1b2", "bogus") is True
    await hass.async_block_till_done()
    assert events == [{"kind": "manual", "source": None}]
    assert entry.runtime_data.feeding.async_feed("ghost") is False
