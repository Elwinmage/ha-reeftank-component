"""The water_test service and the per-chemistry sensors, end to end."""

from __future__ import annotations

from typing import Any

import pytest
from conftest import state_of
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.reeftank.const import DOMAIN
from custom_components.reeftank.monitoring import Monitor


async def test_water_test_service_records(
    hass: HomeAssistant, saved: dict[str, Any], entry: MockConfigEntry
) -> None:
    """A recorded test shows on its chemistry sensor, with redsea's links."""
    data = entry.runtime_data
    await hass.services.async_call(
        DOMAIN,
        "water_test",
        {"aquarium": "a1b2", "parameter": "ca", "value": 430},
        blocking=True,
    )
    await hass.async_block_till_done()

    last = data.monitoring.last_test("a1b2", "ca")
    assert last is not None and last[1] == 430.0

    state = state_of(hass, "sensor.reefer_425_ca")
    assert float(state.state) == 430.0
    assert state.attributes["unit_of_measurement"] == "ppm"
    measurements = state.attributes["measurements"]
    assert measurements[-1]["parameter"] == "ca"
    assert measurements[-1]["value"] == 430.0
    assert state.attributes["tested_at"] is not None
    # Found by redsea the same way as the water volume sensor, marked
    # unambiguously by its chemistry
    assert state.attributes["reef_parameter"] == "ca"
    assert state.attributes["aquarium"] == "a1b2"
    assert "device_ids" in state.attributes
    assert "cloud" in state.attributes


async def test_sensor_empty_without_a_test(
    hass: HomeAssistant, saved: dict[str, Any], entry: MockConfigEntry
) -> None:
    """A chemistry never tested reads unknown, with an empty history."""
    state = state_of(hass, "sensor.reefer_425_mg")
    assert state.state in ("unknown", "unavailable")
    assert state.attributes["measurements"] == []
    assert state.attributes["tested_at"] is None


async def test_unknown_aquarium_reads_nothing(
    hass: HomeAssistant, saved: dict[str, Any], entry: MockConfigEntry
) -> None:
    """Reading an aquarium that has no monitor yet is safe."""
    monitoring = entry.runtime_data.monitoring
    assert monitoring.last_test("zzzz", "kh") is None
    assert monitoring.tests_of("zzzz", "kh") == []


async def test_kh_falls_back_to_external_tests(
    hass: HomeAssistant, saved: dict[str, Any], entry: MockConfigEntry
) -> None:
    """KH uses the tests read from an entity until one is recorded."""
    monitoring = entry.runtime_data.monitoring
    monitor = monitoring._monitors.setdefault("a1b2", Monitor())
    monitor.kh_tests = [(100.0, 7.8)]
    assert monitoring.last_test("a1b2", "kh") == (100.0, 7.8)
    assert monitoring.tests_of("a1b2", "kh") == [(100.0, 7.8)]
    # A recorded test wins over the external one
    monitor.record_test("kh", 200.0, 8.1, 100)
    assert monitoring.last_test("a1b2", "kh") == (200.0, 8.1)
    assert monitoring.tests_of("a1b2", "kh") == [(200.0, 8.1)]


async def test_unknown_aquarium_raises(
    hass: HomeAssistant, saved: dict[str, Any], entry: MockConfigEntry
) -> None:
    """An unknown aquarium reference is rejected."""
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "water_test",
            {"aquarium": "nope", "parameter": "kh", "value": 8.0},
            blocking=True,
        )
