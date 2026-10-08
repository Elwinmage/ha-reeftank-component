"""Persistence of the documents."""

from __future__ import annotations

from typing import Any

import pytest
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from custom_components.reeftank.const import (
    SIGNAL_AQUARIUM_ADDED,
    SIGNAL_AQUARIUM_UPDATED,
    SIGNAL_AQUARIUMS_CHANGED,
    STORE_KEY,
)
from custom_components.reeftank.store import AquariumStore, RevisionConflict


async def test_load_skips_invalid(
    hass: HomeAssistant, hass_storage: dict[str, Any], document: dict[str, Any]
) -> None:
    hass_storage[STORE_KEY] = {
        "version": 1,
        "key": STORE_KEY,
        "data": {"aquariums": {"good": document, "bad": {"name": ""}}},
    }
    store = AquariumStore(hass)
    await store.async_load()
    assert store.ids() == ["good"]
    good = store.get("good")
    assert good is not None and good["id"] == "good"


async def test_load_empty(hass: HomeAssistant) -> None:
    store = AquariumStore(hass)
    await store.async_load()
    assert store.ids() == [] and store.all() == []
    assert store.get("x") is None


async def test_save_signals_and_revisions(
    hass: HomeAssistant, hass_storage: dict[str, Any], document: dict[str, Any]
) -> None:
    store = AquariumStore(hass)
    await store.async_load()
    added: list[str] = []
    updated: list[Any] = []
    changed: list[bool] = []
    async_dispatcher_connect(hass, SIGNAL_AQUARIUM_ADDED, added.append)
    async_dispatcher_connect(
        hass, SIGNAL_AQUARIUMS_CHANGED, lambda: changed.append(True)
    )

    doc = store.save(document)
    aquarium_id = doc["id"]
    async_dispatcher_connect(
        hass, SIGNAL_AQUARIUM_UPDATED.format(aquarium_id), updated.append
    )
    await hass.async_block_till_done()
    assert added == [aquarium_id]
    assert doc["revision"] == 1

    doc["name"] = "Renamed"
    doc2 = store.save(doc, expected_revision=1)
    await hass.async_block_till_done()
    assert doc2["revision"] == 2
    assert updated[-1]["name"] == "Renamed"
    assert added == [aquarium_id], "an update is not a creation"

    with pytest.raises(RevisionConflict) as err:
        store.save(doc, expected_revision=1)
    assert err.value.current["revision"] == 2

    with pytest.raises(vol.Invalid):
        store.save({"id": aquarium_id, "name": ""})

    # a client-chosen id is kept on creation
    assert store.save({"id": "mine", "name": "Mine"})["id"] == "mine"
    assert store.find("renamed") == aquarium_id
    assert store.find("mine") == "mine"
    assert store.find("ghost") is None

    assert store.delete(aquarium_id) is True
    await hass.async_block_till_done()
    assert updated[-1] is None
    assert store.delete(aquarium_id) is False
    assert changed

    await store.async_flush()
    assert list(hass_storage[STORE_KEY]["data"]["aquariums"]) == ["mine"]
