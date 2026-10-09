"""Fixtures of the ReefTank tests (pytest-homeassistant-custom-component)."""

from __future__ import annotations

import sys
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

DOMAIN = "reeftank"


MANIFEST_URL = (
    "https://github.com/Elwinmage/reeftank-catalog/releases/latest/download/"
    "manifest.json"
)


@pytest.fixture(autouse=True)
def _auto_enable_custom_integrations(enable_custom_integrations: Any) -> None:
    """Load this repo's custom_components in the test instance."""
    return


@pytest.fixture(autouse=True)
def _isolated_config(hass: HomeAssistant, tmp_path: Path) -> None:
    """Write <config>/reeftank/ in a fresh folder for every test."""
    hass.config.config_dir = str(tmp_path / "config")


@pytest.fixture(autouse=True)
def _no_catalog_release(aioclient_mock: Any) -> Any:
    """GitHub unreachable unless a test publishes a release."""
    aioclient_mock.get(MANIFEST_URL, status=404)
    return aioclient_mock


def sample_document(**overrides: Any) -> dict[str, Any]:
    """A complete, valid aquarium document."""
    doc: dict[str, Any] = {
        "name": "Reefer 425",
        "dimensions_cm": {"length": 121.9, "width": 60.9, "height": 40.6},
        "waters": {
            "main": {
                "lights": [{"device_id": "led1", "x": 0.3}],
                "flow": ["number.wave_speed"],
                "livestock": [
                    {
                        "id": "l1",
                        "species": "chromis_viridis",
                        "count": 7,
                        "size_cm": [8, 5],
                    },
                    {"id": "l2", "species": "mandarin", "count": 1},
                    {
                        "id": "l3",
                        "kind": "invertebrate",
                        "species": "cleaner_shrimp",
                        "count": 2,
                    },
                ],
                "corals": [
                    {
                        "id": "c1",
                        "species": "euphyllia",
                        "view": "front",
                        "pos": [0.4, 0.7],
                        "palette": ["#5C2D91", "#9be564"],
                    }
                ],
            },
            "sump": {"lights": [{"entity_id": "light.refugium"}]},
        },
        "feeding": {
            "sources": [
                {"id": "f1", "entity_id": "sensor.feeder_last_feed"},
                {"id": "rs", "entity_id": "switch.feeding"},
            ]
        },
        "views": {
            "front": {
                "image": "a1b2/0123456789abcdef.webp",
                "regions": [
                    {
                        "water": "main",
                        "quad": [[0.1, 0.1], [0.9, 0.1], [0.9, 0.6], [0.1, 0.6]],
                    }
                ],
                "decor": [{"id": "d1", "z": 0.2, "poly": [[0, 0], [1, 0], [1, 1]]}],
                "elements": [
                    {
                        "id": "e1",
                        "kind": "device",
                        "device_id": "led1",
                        "pos": [0.3, 0.05],
                    },
                    {
                        "id": "e2",
                        "kind": "device",
                        "device_id": "feeder1",
                        "pos": [0.6, 0.05],
                        "roles": ["feeding_point"],
                        "source": "f1",
                    },
                    {
                        "id": "e3",
                        "kind": "entity",
                        "entity_id": "sensor.temp",
                        "type": "common-sensor",
                        "pos": [0.8, 0.6],
                    },
                ],
                "hotspots": [
                    {
                        "id": "h1",
                        "poly": [[0, 0.6], [1, 0.6], [1, 1]],
                        "goto": "cabinet",
                    }
                ],
            },
            "cabinet": {"regions": [{"water": "sump"}]},
        },
    }
    doc.update(overrides)
    return doc


def state_of(hass: HomeAssistant, entity_id: str) -> Any:
    """The state of an entity, which must exist."""
    state = hass.states.get(entity_id)
    assert state is not None, entity_id
    return state


@pytest.fixture
def document() -> dict[str, Any]:
    """A valid document (fresh copy for every test)."""
    return sample_document()


@pytest.fixture
async def entry(hass: HomeAssistant) -> AsyncGenerator[MockConfigEntry]:
    """The integration set up with one config entry."""
    assert await async_setup_component(hass, "http", {})
    config_entry = MockConfigEntry(domain=DOMAIN, title="ReefTank", data={})
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    yield config_entry


@pytest.fixture
async def saved(hass: HomeAssistant, entry: MockConfigEntry) -> dict[str, Any]:
    """The sample document saved in the integration (id `a1b2`)."""
    doc = await entry.runtime_data.async_save({**sample_document(), "id": "a1b2"})
    await hass.async_block_till_done()
    return doc
