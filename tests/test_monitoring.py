"""Sampling, history and entities of the monitoring."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import timedelta
from typing import Any
from unittest.mock import patch

import pytest
from conftest import sample_document, state_of
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.reeftank.analysis import DAY_S, HOUR_S, STEP_S, Series
from custom_components.reeftank.const import DOMAIN
from custom_components.reeftank.monitoring import Channel, Monitor, _configured

PH = "sensor.tank_ph"
ORP = "sensor.tank_orp"
CO2 = "sensor.room_co2"
PH_CAL = "sensor.tank_ph_last_adjustment"
PAUSE = "switch.ph_probe_maintenance"
ALARM = "binary_sensor.reefer_425_ph_below_its_usual_level"
STATUS = "sensor.reefer_425_water_monitoring"
PAUSE_SWITCH = "switch.reefer_425_pause_monitoring"


@pytest.fixture
async def tank(
    hass: HomeAssistant, entry: MockConfigEntry, saved: dict[str, Any]
) -> AsyncGenerator[Any]:
    """The sample aquarium, monitored, with live probes."""
    hass.states.async_set(PH, "8.2")
    hass.states.async_set(ORP, "350")
    hass.states.async_set(CO2, "900")
    await hass.services.async_call(
        DOMAIN,
        "monitoring_configure",
        {
            "aquarium": "a1b2",
            "ph_entity": PH,
            "orp_entity": ORP,
            "co2_entity": CO2,
            "ph_calibration_entity": PH_CAL,
            "pause_entities": [PAUSE],
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    yield entry.runtime_data


async def tick(hass: HomeAssistant, data: Any, at: Any = None) -> None:
    """Run one sampling round."""
    await data.monitoring._async_tick(at or dt_util.utcnow())
    await hass.async_block_till_done()


def channel(data: Any, name: str = "ph") -> Channel:
    """A channel of the sample aquarium."""
    return data.monitoring._monitors["a1b2"].channels[name]


def history(data: Any, name: str, value: float, days: float = 16) -> None:
    """Fill a channel with a flat history ending now."""
    now = dt_util.utcnow().timestamp()
    series = Series()
    wave = (0.0, 0.1, 0.0, -0.1) if name == "ph" else (0.0, 5.0, 0.0, -5.0)
    for index in range(int(days * DAY_S / STEP_S), 0, -1):
        series.add(now - index * STEP_S, value + wave[index // 72 % 4])
    channel(data, name).series = series


def test_configured() -> None:
    """CO2 alone is nothing to analyse."""
    assert not _configured({"co2_entity": CO2})
    assert _configured({"orp_entity": ORP})


async def test_not_configured(
    hass: HomeAssistant, saved: dict[str, Any], entry: MockConfigEntry
) -> None:
    """An aquarium without probes has unavailable-free, quiet entities."""
    assert state_of(hass, STATUS).state == "not_configured"
    assert state_of(hass, ALARM).state == "unknown"
    assert state_of(hass, PAUSE_SWITCH).state == "off"
    await tick(hass, entry.runtime_data)
    assert entry.runtime_data.monitoring.report("a1b2") == {}


async def test_entities_known_by_the_card(
    hass: HomeAssistant, saved: dict[str, Any], entry: MockConfigEntry
) -> None:
    """The card gets the ids of the monitoring entities."""
    ids = entry.runtime_data.entity_ids("a1b2")
    assert ids["ph_base_low"] == ALARM
    assert ids["monitoring"] == STATUS
    assert ids["monitoring_pause"] == PAUSE_SWITCH


async def test_sampling_on_schedule(hass: HomeAssistant, tank: Any) -> None:
    """Samples are taken every five minutes, and rounded."""
    hass.states.async_set(PH, "8.20049")
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=STEP_S + 1))
    await hass.async_block_till_done(wait_background_tasks=True)
    assert channel(tank).series.values == [8.2]
    assert state_of(hass, STATUS).state == "learning"
    assert state_of(hass, ALARM).state == "unknown"


@pytest.mark.parametrize("state", ["unavailable", "unknown", "", "abc", "nan", "inf"])
async def test_invalid_readings(hass: HomeAssistant, tank: Any, state: str) -> None:
    """Anything but a number leaves a gap."""
    await tick(hass, tank)
    hass.states.async_set(PH, state)
    await tick(hass, tank, dt_util.utcnow() + timedelta(seconds=STEP_S))
    assert channel(tank).series.values == [8.2, None]


async def test_entity_gone(hass: HomeAssistant, tank: Any) -> None:
    """An entity that disappeared leaves a gap."""
    await tick(hass, tank)
    hass.states.async_remove(PH)
    await tick(hass, tank, dt_util.utcnow() + timedelta(seconds=STEP_S))
    assert channel(tank).series.values == [8.2, None]


async def test_alarm_published(hass: HomeAssistant, tank: Any) -> None:
    """A drop of the pH turns the alarm on, with what explains it."""
    await tick(hass, tank)
    history(tank, "ph", 8.2)
    history(tank, "orp", 350)
    series = channel(tank).series
    last_day = len(series) - DAY_S // STEP_S
    series.values[last_day:] = [
        v - 0.2 if v is not None else None for v in series.values[last_day:]
    ]
    await tank.monitoring._async_analyze("a1b2", dt_util.utcnow().timestamp())
    await hass.async_block_till_done()

    state = state_of(hass, ALARM)
    assert state.state == "on"
    assert state.attributes["device_class"] == "problem"
    assert state.attributes["cause"] == "unknown"
    assert state.attributes["drop"] == pytest.approx(0.2, abs=0.02)
    assert state_of(hass, STATUS).state == "ready"
    assert state_of(hass, STATUS).attributes["learning_pct"] == 100
    assert float(state_of(hass, "sensor.reefer_425_ph_24_h_mean").state) == (
        pytest.approx(8.0, abs=0.02)
    )
    assert float(state_of(hass, "sensor.reefer_425_ph_swing_24_h").state) > 0
    assert (
        state_of(hass, "sensor.reefer_425_orp_without_the_ph_effect").state != "unknown"
    )
    assert tank.monitoring._monitors["a1b2"].alarms["ph_base_low"] is True


async def test_probe_alarm_entity(hass: HomeAssistant, tank: Any) -> None:
    """The reasons of a suspect probe are given per probe."""
    await tick(hass, tank)
    history(tank, "ph", 8.2, days=1)
    history(tank, "orp", 350, days=1)
    channel(tank).series.values[-200:] = [8.2] * 200
    await tank.monitoring._async_analyze("a1b2", dt_util.utcnow().timestamp())
    await hass.async_block_till_done()
    state = state_of(hass, "binary_sensor.reefer_425_suspect_probe")
    assert state.state == "on"
    assert state.attributes["probes"] == {"ph": ["frozen"]}


async def test_other_alarms_details(hass: HomeAssistant, tank: Any) -> None:
    """The other alarms show their figures."""
    await tick(hass, tank)
    history(tank, "ph", 8.2)
    history(tank, "orp", 350)
    await tank.monitoring._async_analyze("a1b2", dt_util.utcnow().timestamp())
    await hass.async_block_till_done()
    swing = state_of(hass, "binary_sensor.reefer_425_ph_swing_wider_than_usual")
    assert "swing_baseline" in swing.attributes
    profile = state_of(hass, "binary_sensor.reefer_425_ph_day_pattern_disturbed")
    assert "profile_hours_off" in profile.attributes
    orp = state_of(hass, "binary_sensor.reefer_425_orp_below_its_usual_level")
    assert "baseline" in orp.attributes


async def test_user_pause(hass: HomeAssistant, tank: Any) -> None:
    """The pause leaves gaps, hides the alarms and ends by itself."""
    await tick(hass, tank)
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": PAUSE_SWITCH}, blocking=True
    )
    await hass.async_block_till_done()
    assert state_of(hass, PAUSE_SWITCH).state == "on"
    assert state_of(hass, PAUSE_SWITCH).attributes["until"]
    assert state_of(hass, STATUS).state == "paused"
    assert tank.monitoring.alarm("a1b2", "probe_suspect") is None

    await tick(hass, tank, dt_util.utcnow() + timedelta(seconds=STEP_S))
    assert channel(tank).series.values == [8.2, None]

    # Past the 6 default hours, sampling is back
    await tick(hass, tank, dt_util.utcnow() + timedelta(hours=7))
    assert state_of(hass, PAUSE_SWITCH).state == "off"
    assert channel(tank).series.values[-1] == 8.2


async def test_pause_turned_off(hass: HomeAssistant, tank: Any) -> None:
    """The switch resumes right away."""
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": PAUSE_SWITCH}, blocking=True
    )
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": PAUSE_SWITCH}, blocking=True
    )
    await hass.async_block_till_done()
    assert state_of(hass, PAUSE_SWITCH).state == "off"
    assert tank.monitoring.user_paused_until("a1b2") is None


async def test_paused_by_entity(hass: HomeAssistant, tank: Any) -> None:
    """A probe maintenance switch pauses too, for as long as it is on."""
    await tick(hass, tank)
    hass.states.async_set(PAUSE, "on")
    await tick(hass, tank, dt_util.utcnow() + timedelta(seconds=STEP_S))
    assert tank.monitoring.status("a1b2") == "paused"
    assert channel(tank).series.values == [8.2, None]
    hass.states.async_set(PAUSE, "off")
    assert tank.monitoring.status("a1b2") == "learning"


async def test_calibration_carries_history_over(hass: HomeAssistant, tank: Any) -> None:
    """A calibration blanks the probe's last hours, then shifts the past."""
    hass.states.async_set(PH_CAL, "2026-10-01T10:00:00+00:00")
    await tick(hass, tank)
    history(tank, "ph", 8.0, days=3)
    history(tank, "orp", 350, days=3)
    start = dt_util.utcnow()

    hass.states.async_set(PH_CAL, "2026-11-01T10:00:00+00:00")
    await tick(hass, tank, start + timedelta(seconds=STEP_S))
    state = channel(tank)
    since = state.settling_since
    assert since is not None
    assert tank.monitoring.status("a1b2") == "settling"
    assert tank.monitoring.alarm("a1b2", "ph_base_low") is None
    assert tank.monitoring.alarm("a1b2", "probe_suspect") is False
    assert state.series.window(since - HOUR_S, since) == [None] * 12

    # The calibrated probe reads 0.1 higher for a day
    for step in range(2, 24 * 12 + 3):
        hass.states.async_set(PH, "8.1")
        await tank.monitoring._async_tick(start + timedelta(seconds=STEP_S * step))
    await hass.async_block_till_done()
    assert state.settling_since is None
    old = [v for v in state.series.window(since - 2 * DAY_S, since - DAY_S) if v]
    assert sum(old) / len(old) == pytest.approx(8.1, abs=0.02)


async def test_calibration_without_data_relearns(
    hass: HomeAssistant, tank: Any
) -> None:
    """Without readings around a calibration, its effect stays unknown."""
    hass.states.async_set(PH_CAL, "one")
    await tick(hass, tank)
    hass.states.async_set(PH_CAL, "two")
    start = dt_util.utcnow()
    await tick(hass, tank, start + timedelta(seconds=STEP_S))
    assert channel(tank).settling_since is not None
    await tick(hass, tank, start + timedelta(hours=25))
    state = channel(tank)
    assert state.settling_since is None
    assert state.series.first_time() is None


async def test_calibration_entity_invalid(hass: HomeAssistant, tank: Any) -> None:
    """A date coming back after a restart is no calibration."""
    hass.states.async_set(PH_CAL, "unavailable")
    await tick(hass, tank)
    assert channel(tank).calibration is None
    hass.states.async_set(PH_CAL, "one")
    await tick(hass, tank, dt_util.utcnow() + timedelta(seconds=STEP_S))
    hass.states.async_set(PH_CAL, "unavailable")
    await tick(hass, tank, dt_util.utcnow() + timedelta(seconds=STEP_S * 2))
    hass.states.async_set(PH_CAL, "one")
    await tick(hass, tank, dt_util.utcnow() + timedelta(seconds=STEP_S * 3))
    assert channel(tank).settling_since is None


async def test_entity_changed_forgets(hass: HomeAssistant, tank: Any) -> None:
    """Another probe has another history."""
    await tick(hass, tank)
    hass.states.async_set("sensor.other_ph", "7.9")
    await hass.services.async_call(
        DOMAIN,
        "monitoring_configure",
        {"aquarium": "a1b2", "ph_entity": "sensor.other_ph"},
        blocking=True,
    )
    await tick(hass, tank, dt_util.utcnow() + timedelta(seconds=STEP_S))
    assert channel(tank).series.values == [7.9]
    assert channel(tank, "orp").series.values == [350.0, 350.0]


async def test_configure_keeps_the_rest(hass: HomeAssistant, tank: Any) -> None:
    """A call changes what it names, and thresholds are checked."""
    await hass.services.async_call(
        DOMAIN,
        "monitoring_configure",
        {"aquarium": "Reefer 425", "orp_drop_mv": 45, "co2_entity": None},
        blocking=True,
    )
    config = tank.store.get("a1b2")["monitoring"]
    assert config["orp_drop_mv"] == 45
    assert config["ph_entity"] == PH
    assert config["co2_entity"] is None
    with pytest.raises(Exception, match="value must be at most"):
        await hass.services.async_call(
            DOMAIN,
            "monitoring_configure",
            {"aquarium": "a1b2", "orp_drop_mv": 1000},
            blocking=True,
        )


async def test_configure_unknown_aquarium(hass: HomeAssistant, tank: Any) -> None:
    """The aquarium has to exist."""
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "monitoring_configure", {"aquarium": "nope"}, blocking=True
        )


async def test_unconfigured_clears_the_report(hass: HomeAssistant, tank: Any) -> None:
    """Probes removed: back to not configured."""
    await tick(hass, tank)
    await hass.services.async_call(
        DOMAIN,
        "monitoring_configure",
        {"aquarium": "a1b2", "ph_entity": None, "orp_entity": None},
        blocking=True,
    )
    await tick(hass, tank, dt_util.utcnow() + timedelta(seconds=STEP_S))
    assert tank.monitoring.report("a1b2") == {}
    assert state_of(hass, STATUS).state == "not_configured"
    assert channel(tank).series.first_time() is None


async def test_reset(hass: HomeAssistant, tank: Any) -> None:
    """The history is forgotten, for one measure or all."""
    await tick(hass, tank)
    tank.monitoring._monitors["a1b2"].alarms["ph_base_low"] = True
    await hass.services.async_call(
        DOMAIN,
        "monitoring_reset",
        {"aquarium": "a1b2", "channel": "ph"},
        blocking=True,
    )
    assert channel(tank).series.first_time() is None
    assert channel(tank, "orp").series.first_time() is not None
    assert tank.monitoring._monitors["a1b2"].alarms == {
        "probe_suspect": False,
    }
    await hass.services.async_call(
        DOMAIN, "monitoring_reset", {"aquarium": "a1b2"}, blocking=True
    )
    assert channel(tank, "orp").series.first_time() is None


async def test_history_survives_a_restart(
    hass: HomeAssistant, tank: Any, entry: MockConfigEntry
) -> None:
    """The history comes back with the integration, and analysed."""
    await tick(hass, tank)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    data = entry.runtime_data
    assert channel(data).series.values == [8.2]
    assert data.monitoring.report("a1b2")["learning"] < 1


async def test_analysis_not_blocked_by_a_deleted_aquarium(
    hass: HomeAssistant, tank: Any
) -> None:
    """Deleting an aquarium drops its history."""
    await tick(hass, tank)
    assert await tank.async_delete("a1b2")
    await hass.async_block_till_done()
    assert tank.monitoring.status("a1b2") == "not_configured"
    assert tank.monitoring.report("a1b2") == {}
    assert tank.monitoring.user_paused_until("a1b2") is None
    await tank.monitoring._async_analyze("a1b2", 0)
    tank.monitoring.async_remove("a1b2")


async def test_load_drops_deleted_aquariums(hass: HomeAssistant, tank: Any) -> None:
    """A history without its aquarium is not restored."""
    await tick(hass, tank)
    stored = tank.monitoring._stored()
    stored["aquariums"]["gone"] = Monitor().as_dict()
    with patch.object(tank.monitoring._store, "async_load", return_value=stored):
        tank.monitoring._monitors.clear()
        await tank.monitoring.async_load()
    assert set(tank.monitoring._monitors) == {"a1b2"}


async def test_stop_twice(hass: HomeAssistant, tank: Any) -> None:
    """Stopping is safe once stopped."""
    tank.monitoring.async_stop()
    tank.monitoring.async_stop()


async def test_new_aquarium_gets_entities(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    """An aquarium created later is monitored like the others."""
    assert await async_setup_component(hass, "http", {})
    await entry.runtime_data.async_save({**sample_document(name="Nano"), "id": "b2"})
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    assert registry.async_get_entity_id("binary_sensor", DOMAIN, "b2_orp_low")
    assert registry.async_get_entity_id("switch", DOMAIN, "b2_monitoring_pause")


KH = "sensor.head_last_measurement"


async def set_kh(hass: HomeAssistant) -> None:
    """Add the KH tests to the monitored aquarium."""
    await hass.services.async_call(
        DOMAIN,
        "monitoring_configure",
        {"aquarium": "a1b2", "kh_entity": KH},
        blocking=True,
    )


def measurement(days: float, value: Any, **extra: Any) -> dict[str, Any]:
    """A test of the history of a dosing head."""
    at = dt_util.utcnow() - timedelta(days=days)
    return {"at": at.isoformat(), "parameter": "kh", "value": value, **extra}


async def test_kh_tests_from_the_history(hass: HomeAssistant, tank: Any) -> None:
    """The history of the entity is taken at once, without unusable tests."""
    hass.states.async_set(
        KH,
        "7.2",
        {
            "unit_of_measurement": "dKH",
            "measurements": [
                measurement(8, 8.0),
                measurement(7, 3.0, suspect=True),
                measurement(6, 430, parameter="ca"),
                measurement(5, "x"),
                {"at": "not a date", "value": 8.0},
                "junk",
                measurement(1, 7.2),
            ],
        },
    )
    await set_kh(hass)
    await tick(hass, tank)
    monitor = tank.monitoring._monitors["a1b2"]
    assert [value for _at, value in monitor.kh_tests] == [8.0, 7.2]

    state = state_of(hass, "binary_sensor.reefer_425_kh_moving_too_fast")
    assert state.state == "on"
    assert state.attributes["last"] == 7.2
    assert state.attributes["change"] == pytest.approx(-0.8)


async def test_kh_alarm_and_estimate_entities(hass: HomeAssistant, tank: Any) -> None:
    """A recent test gives an estimate, hidden during a calibration."""
    hass.states.async_set(
        KH, "8.0", {"measurements": [measurement(2, 8.0), measurement(1, 8.0)]}
    )
    await set_kh(hass)
    hass.states.async_set(PH_CAL, "one")
    await tick(hass, tank)
    history(tank, "ph", 8.2)
    history(tank, "orp", 350)
    history(tank, "co2", 900)
    await tank.monitoring._async_analyze("a1b2", dt_util.utcnow().timestamp())
    await hass.async_block_till_done()
    estimated = state_of(hass, "sensor.reefer_425_kh_estimated")
    assert float(estimated.state) == pytest.approx(8.0, abs=0.3)
    assert estimated.attributes["last_test"] == 8.0
    assert state_of(hass, ALARM).attributes["kh_test_due"] is False

    hass.states.async_set(PH_CAL, "two")
    await tick(hass, tank, dt_util.utcnow() + timedelta(seconds=STEP_S))
    assert state_of(hass, "sensor.reefer_425_kh_estimated").state == "unknown"
    assert tank.monitoring.alarm("a1b2", "kh_fast_change") is False


async def test_kh_from_a_plain_entity(hass: HomeAssistant, tank: Any) -> None:
    """Without a history, each new value is a test, and a restart is not."""
    hass.states.async_set(KH, "8.0")
    await set_kh(hass)
    await tick(hass, tank)
    await tick(hass, tank, dt_util.utcnow() + timedelta(seconds=STEP_S))
    monitor = tank.monitoring._monitors["a1b2"]
    assert [value for _at, value in monitor.kh_tests] == [8.0]
    hass.states.async_set(KH, "abc")
    await tick(hass, tank, dt_util.utcnow() + timedelta(seconds=STEP_S * 2))
    assert len(monitor.kh_tests) == 1

    later = dt_util.utcnow() + timedelta(days=1)
    with patch("homeassistant.core.dt_util.utcnow", return_value=later):
        hass.states.async_set(KH, "7.9")
    await tick(hass, tank, later)
    assert [value for _at, value in monitor.kh_tests] == [8.0, 7.9]


async def test_kh_ignores_another_unit(hass: HomeAssistant, tank: Any) -> None:
    """A head dosing calcium is no KH."""
    hass.states.async_set(KH, "430", {"unit_of_measurement": "ppm"})
    await set_kh(hass)
    await tick(hass, tank)
    assert tank.monitoring._monitors["a1b2"].kh_tests == []
    assert state_of(hass, "sensor.reefer_425_kh_estimated").state == "unknown"


async def test_kh_entity_changed_forgets(hass: HomeAssistant, tank: Any) -> None:
    """Another entity has other tests, and the reset forgets them."""
    hass.states.async_set(KH, "8.0")
    await set_kh(hass)
    await tick(hass, tank)
    monitor = tank.monitoring._monitors["a1b2"]
    assert monitor.kh_tests

    await hass.services.async_call(
        DOMAIN,
        "monitoring_configure",
        {"aquarium": "a1b2", "kh_entity": None},
        blocking=True,
    )
    await tick(hass, tank, dt_util.utcnow() + timedelta(seconds=STEP_S))
    assert monitor.kh_tests == []

    await set_kh(hass)
    await tick(hass, tank, dt_util.utcnow() + timedelta(seconds=STEP_S * 2))
    assert monitor.kh_tests
    await hass.services.async_call(
        DOMAIN,
        "monitoring_reset",
        {"aquarium": "a1b2", "channel": "kh"},
        blocking=True,
    )
    assert monitor.kh_tests == []
    assert channel(tank).series.first_time() is not None


async def test_kh_tests_survive_a_restart(
    hass: HomeAssistant, tank: Any, entry: MockConfigEntry
) -> None:
    """The tests are stored with the history."""
    hass.states.async_set(KH, "8.0")
    await set_kh(hass)
    await tick(hass, tank)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    monitor = entry.runtime_data.monitoring._monitors["a1b2"]
    assert [value for _at, value in monitor.kh_tests] == [8.0]
    assert monitor.kh_entity == KH
