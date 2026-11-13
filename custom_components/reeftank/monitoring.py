"""Monitoring: sample the probes of every aquarium and keep them analysed.

The sampling and the history live here, server side, so nothing is lost when
no card is open. The history has a `Store` of its own: it changes every five
minutes, and the aquarium document must only change when somebody edits it.

The rules themselves are in analysis.py. See doc/en/technical.md, "Monitoring".
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from math import isfinite
from statistics import fmean
from typing import TYPE_CHECKING, Any, cast

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .analysis import (
    ALARM_KH,
    ALARM_PROBE,
    ALARMS,
    DAY_S,
    HOUR_S,
    STEP_S,
    KhTest,
    Series,
    analyze,
    covered,
    valid,
)
from .const import (
    CHANNEL_CO2,
    CHANNEL_KH,
    CHANNEL_ORP,
    CHANNEL_PH,
    CHANNELS,
    MONITORING_STORE_KEY,
    MONITORING_STORE_VERSION,
    PROBE_CHANNELS,
    SIGNAL_MONITORING,
    STATUS_LEARNING,
    STATUS_NOT_CONFIGURED,
    STATUS_PAUSED,
    STATUS_READY,
    STATUS_SETTLING,
    TESTS_KEPT,
)

if TYPE_CHECKING:
    from .store import AquariumStore

_LOGGER = logging.getLogger(__name__)

# Decimals worth keeping: they make up most of the size of the history.
_DECIMALS = {CHANNEL_PH: 3, CHANNEL_ORP: 1, CHANNEL_CO2: 0}
# Days kept on top of the learning period (the last 24 hours, and a margin).
_EXTRA_DAYS = 2
# The history is written this often: losing a few samples to a crash is fine.
_SAVE_DELAY_S = 900
# A calibration is noticed once finished: the probe left the water before.
_CALIBRATION_BLANK_S = 2 * HOUR_S
# A calibrated probe reads a new level; how long to measure it.
_SETTLE_S = DAY_S
_INVALID = (None, "", STATE_UNAVAILABLE, STATE_UNKNOWN)
# KH tests kept: three months at one a day, a year and more at one a week
_KH_TESTS = 100
_KH_UNIT = "dkh"
_KH_DECIMALS = 2


@dataclass
class Channel:
    """History of one measure of an aquarium."""

    entity_id: str | None = None
    series: Series = field(default_factory=Series)
    # Last state of the calibration entity
    calibration: str | None = None
    # When the last calibration was noticed, until its effect is measured
    settling_since: float | None = None

    def reset(self) -> None:
        """Forget the history: it says nothing about what is measured now."""
        self.series = Series()
        self.settling_since = None

    def as_dict(self) -> dict[str, Any]:
        """Stored form."""
        return {
            "entity_id": self.entity_id,
            "series": self.series.as_dict(),
            "calibration": self.calibration,
            "settling_since": self.settling_since,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Channel:
        """Read the stored form."""
        return cls(
            data.get("entity_id"),
            Series.from_dict(data.get("series") or {}),
            data.get("calibration"),
            data.get("settling_since"),
        )


@dataclass
class Monitor:
    """Monitoring state of one aquarium."""

    channels: dict[str, Channel] = field(
        default_factory=lambda: {channel: Channel() for channel in CHANNELS}
    )
    paused_until: float | None = None
    # Last known value of each alarm, to latch them
    alarms: dict[str, bool] = field(default_factory=dict[str, bool])
    report: dict[str, Any] = field(default_factory=dict[str, Any])
    kh_entity: str | None = None
    kh_tests: list[KhTest] = field(default_factory=list[KhTest])
    # Water tests recorded in the aquarium, by chemistry: (epoch, value) pairs.
    # The canonical home of a hand-entered result, exposed one sensor each.
    tests: dict[str, list[tuple[float, float]]] = field(
        default_factory=dict[str, list[tuple[float, float]]]
    )

    def record_test(self, parameter: str, at: float, value: float, keep: int) -> None:
        """Keep a recorded test, one value per timestamp, newest ``keep``."""
        merged = dict(self.tests.get(parameter, []))
        merged[at] = value
        self.tests[parameter] = sorted(merged.items())[-keep:]

    def recorded(self, parameter: str) -> list[tuple[float, float]]:
        """The recorded tests of a chemistry (empty when none)."""
        return self.tests.get(parameter, [])

    def last_recorded(self, parameter: str) -> tuple[float, float] | None:
        """The latest recorded test of a chemistry, None when none."""
        series = self.tests.get(parameter)
        return series[-1] if series else None

    def as_dict(self) -> dict[str, Any]:
        """Stored form."""
        return {
            "channels": {k: v.as_dict() for k, v in self.channels.items()},
            "paused_until": self.paused_until,
            "alarms": self.alarms,
            "report": self.report,
            "kh_entity": self.kh_entity,
            "kh_tests": [list(test) for test in self.kh_tests],
            "tests": {
                parameter: [list(test) for test in series]
                for parameter, series in self.tests.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Monitor:
        """Read the stored form."""
        monitor = cls(
            paused_until=data.get("paused_until"),
            alarms=dict(data.get("alarms") or {}),
            report=dict(data.get("report") or {}),
            kh_entity=data.get("kh_entity"),
            kh_tests=[(test[0], test[1]) for test in data.get("kh_tests") or []],
            tests=_load_tests(data.get("tests")),
        )
        for channel, stored in (data.get("channels") or {}).items():
            monitor.channels[channel] = Channel.from_dict(stored)
        return monitor


class MonitoringManager:
    """Samples, history and alarms of all the aquariums."""

    def __init__(self, hass: HomeAssistant, store: AquariumStore) -> None:
        """Create the manager; load it, then start it."""
        self._hass = hass
        self._documents = store
        self._store: Store[dict[str, Any]] = Store(
            hass, MONITORING_STORE_VERSION, MONITORING_STORE_KEY
        )
        self._monitors: dict[str, Monitor] = {}
        self._cancel: Callable[[], None] | None = None

    # -- Lifecycle -----------------------------------------------------------

    async def async_load(self) -> None:
        """Read the history from disk, dropping aquariums that are gone."""
        stored = await self._store.async_load() or {}
        known = set(self._documents.ids())
        for aquarium_id, data in (stored.get("aquariums") or {}).items():
            if aquarium_id in known:
                self._monitors[aquarium_id] = Monitor.from_dict(data)

    @callback
    def async_start(self) -> None:
        """Sample every five minutes.

        No analysis yet: the probes of other integrations may not be back, and
        a restart must not read as a probe gone. The last report stands until
        the first sample.
        """
        self._cancel = async_track_time_interval(
            self._hass, self._async_tick, timedelta(seconds=STEP_S)
        )

    @callback
    def async_stop(self) -> None:
        """Stop sampling."""
        if self._cancel is not None:
            self._cancel()
            self._cancel = None

    async def async_flush(self) -> None:
        """Write the history now (unload, tests)."""
        await self._store.async_save(self._stored())

    @callback
    def _stored(self) -> dict[str, Any]:
        return {"aquariums": {k: v.as_dict() for k, v in self._monitors.items()}}

    @callback
    def _schedule_save(self) -> None:
        self._store.async_delay_save(self._stored, _SAVE_DELAY_S)

    # -- Reading -------------------------------------------------------------

    @callback
    def status(self, aquarium_id: str) -> str:
        """Where the monitoring of an aquarium stands."""
        monitor = self._monitors.get(aquarium_id)
        doc = self._documents.get(aquarium_id)
        if monitor is None or doc is None or not _configured(doc["monitoring"]):
            return STATUS_NOT_CONFIGURED
        if self._paused(monitor, doc["monitoring"]):
            return STATUS_PAUSED
        if any(c.settling_since is not None for c in monitor.channels.values()):
            return STATUS_SETTLING
        if monitor.report.get("learning", 0.0) < 1.0:
            return STATUS_LEARNING
        return STATUS_READY

    @callback
    def report(self, aquarium_id: str) -> dict[str, Any]:
        """The last analysis of an aquarium ({} when there is none)."""
        monitor = self._monitors.get(aquarium_id)
        return monitor.report if monitor is not None else {}

    @callback
    def alarm(self, aquarium_id: str, key: str) -> bool | None:
        """An alarm: on, off, or None when it cannot be told right now."""
        status = self.status(aquarium_id)
        if status in (STATUS_NOT_CONFIGURED, STATUS_PAUSED):
            return None
        # A level just changed by a calibration: only the probe can be judged.
        if status == STATUS_SETTLING and key not in (ALARM_PROBE, ALARM_KH):
            return None
        return self.report(aquarium_id).get("alarms", {}).get(key)

    @callback
    def user_paused_until(self, aquarium_id: str) -> datetime | None:
        """When the pause asked by the user ends, None without a pause."""
        monitor = self._monitors.get(aquarium_id)
        if monitor is None or monitor.paused_until is None:
            return None
        return dt_util.utc_from_timestamp(monitor.paused_until)

    # -- Commands ------------------------------------------------------------

    @callback
    def async_pause(self, aquarium_id: str, paused: bool) -> None:
        """Suspend the analysis for a while, or resume it.

        A pause ends by itself: forgotten after a cleaning, it would otherwise
        silently turn the alarms off for good.
        """
        monitor = self._monitors.setdefault(aquarium_id, Monitor())
        monitor.paused_until = None
        doc = self._documents.get(aquarium_id)
        if paused and doc is not None:
            hours = doc["monitoring"]["pause_hours"]
            monitor.paused_until = dt_util.utcnow().timestamp() + hours * HOUR_S
        self._schedule_save()
        self._notify(aquarium_id)

    async def async_reset(self, aquarium_id: str, channel: str | None = None) -> None:
        """Forget the history and learn again (a new probe, say)."""
        monitor = self._monitors.setdefault(aquarium_id, Monitor())
        for name, state in monitor.channels.items():
            if channel in (None, name):
                state.reset()
        if channel in (None, CHANNEL_KH):
            monitor.kh_tests = []
        monitor.alarms = {}
        await self._async_analyze(aquarium_id, dt_util.utcnow().timestamp())
        self._schedule_save()

    @callback
    def async_remove(self, aquarium_id: str) -> None:
        """Forget an aquarium that was deleted."""
        if self._monitors.pop(aquarium_id, None) is not None:
            self._schedule_save()

    # -- Water tests ---------------------------------------------------------

    @callback
    def async_record_test(
        self, aquarium_id: str, parameter: str, value: float, at: datetime
    ) -> None:
        """Record a hand-entered test result of a chemistry.

        The result is the aquarium's, shared by chemistry; the matching
        sensor refreshes at once so readers (the card, redsea) see it.
        """
        monitor = self._monitors.setdefault(aquarium_id, Monitor())
        monitor.record_test(parameter, at.timestamp(), value, TESTS_KEPT)
        self._schedule_save()
        self._notify(aquarium_id)

    @callback
    def last_test(self, aquarium_id: str, parameter: str) -> tuple[float, float] | None:
        """Latest test of a chemistry: (epoch, value), None when none.

        A recorded result wins; KH falls back to the tests read from an
        external entity, so a probe-less setup still has a value.
        """
        monitor = self._monitors.get(aquarium_id)
        if monitor is None:
            return None
        recorded = monitor.last_recorded(parameter)
        if recorded is not None:
            return recorded
        if parameter == CHANNEL_KH and monitor.kh_tests:
            return monitor.kh_tests[-1]
        return None

    @callback
    def tests_of(self, aquarium_id: str, parameter: str) -> list[tuple[float, float]]:
        """The test history of a chemistry (recorded, else KH fallback)."""
        monitor = self._monitors.get(aquarium_id)
        if monitor is None:
            return []
        recorded = monitor.recorded(parameter)
        if recorded:
            return list(recorded)
        if parameter == CHANNEL_KH:
            return list(monitor.kh_tests)
        return []

    # -- Sampling ------------------------------------------------------------

    async def _async_tick(self, now: datetime) -> None:
        """Take a sample of every aquarium, then analyse them."""
        timestamp = now.timestamp()
        sampled = False
        for doc in self._documents.all():
            config = doc["monitoring"]
            monitor = self._monitors.get(doc["id"])
            if monitor is None:
                if not _configured(config):
                    continue
                monitor = self._monitors.setdefault(doc["id"], Monitor())
            self._sample(monitor, config, timestamp)
            sampled = True
        if sampled:
            await self._async_analyze_all(timestamp)
            self._schedule_save()

    @callback
    def _sample(
        self, monitor: Monitor, config: dict[str, Any], timestamp: float
    ) -> None:
        """Record one value per measure."""
        if monitor.paused_until is not None and timestamp >= monitor.paused_until:
            monitor.paused_until = None
        paused = self._paused(monitor, config)
        keep = (config["learning_days"] + _EXTRA_DAYS) * DAY_S
        for name, channel in monitor.channels.items():
            entity_id = config.get(f"{name}_entity")
            if entity_id != channel.entity_id:
                channel.reset()
                channel.calibration = None
                channel.entity_id = entity_id
            if entity_id is None:
                continue
            value = None if paused else self._read(entity_id, _DECIMALS[name])
            channel.series.add(timestamp, value)
            channel.series.trim(timestamp - keep)
        for name in PROBE_CHANNELS:
            channel = monitor.channels[name]
            self._check_calibration(channel, config, name, timestamp)
            self._settle(channel, timestamp)
        self._read_kh_tests(monitor, config.get("kh_entity"))

    @callback
    def _read_kh_tests(self, monitor: Monitor, entity_id: str | None) -> None:
        """Keep the KH tests an entity gives.

        A test is no sample: it stays valid during a pause, and is taken from
        the history of the entity when it has one, so that the first analysis
        already has tests to compare.
        """
        if entity_id != monitor.kh_entity:
            monitor.kh_entity = entity_id
            monitor.kh_tests = []
        state = self._hass.states.get(entity_id) if entity_id else None
        if state is None or not _in_dkh(state.attributes):
            return
        tests = dict(monitor.kh_tests)
        listed = state.attributes.get("measurements")
        if isinstance(listed, list):
            tests |= dict(_listed_tests(cast(list[Any], listed)))
        else:
            value = self._read(state.entity_id, _KH_DECIMALS)
            last = monitor.kh_tests[-1][1] if monitor.kh_tests else None
            # A restart dates the state anew: only a new value is a new test
            if value is not None and value != last:
                tests[state.last_changed.timestamp()] = value
        monitor.kh_tests = sorted(tests.items())[-_KH_TESTS:]

    @callback
    def _paused(self, monitor: Monitor, config: dict[str, Any]) -> bool:
        return monitor.paused_until is not None or any(
            self._hass.states.is_state(entity_id, "on")
            for entity_id in config["pause_entities"]
        )

    @callback
    def _read(self, entity_id: str, decimals: int) -> float | None:
        """The numeric state of an entity, None when it has none."""
        state = self._hass.states.get(entity_id)
        if state is None or state.state in _INVALID:
            return None
        try:
            value = float(state.state)
        except ValueError:
            return None
        return round(value, decimals) if isfinite(value) else None

    @callback
    def _check_calibration(
        self,
        channel: Channel,
        config: dict[str, Any],
        name: str,
        timestamp: float,
    ) -> None:
        """Drop what a probe read out of the water, and start re-measuring."""
        entity_id = config.get(f"{name}_calibration_entity")
        state = self._hass.states.get(entity_id) if entity_id else None
        if state is None or state.state in _INVALID:
            return
        previous = channel.calibration
        channel.calibration = state.state
        if previous is None or previous == state.state:
            return
        _LOGGER.debug("Calibration of %s noticed", channel.entity_id)
        # The sample just taken is already the calibrated probe's
        channel.series.blank(timestamp - _CALIBRATION_BLANK_S, timestamp)
        channel.settling_since = timestamp

    @callback
    def _settle(self, channel: Channel, timestamp: float) -> None:
        """Carry the history over to the level of a calibrated probe.

        The water did not change, the reading did: the difference between the
        days around the calibration is what it moved by. The whole history
        follows it, rather than two weeks of learning after each calibration.
        """
        since = channel.settling_since
        if since is None or timestamp < since + _SETTLE_S:
            return
        channel.settling_since = None
        series = channel.series
        before = series.window(since - _CALIBRATION_BLANK_S - DAY_S, since)
        after = series.window(since, since + _SETTLE_S)
        # The blanked hours are expected in `before`
        if len(valid(before)) < 0.5 * len(before) or not covered(after):
            channel.reset()
            return
        series.shift_before(since, fmean(valid(after)) - fmean(valid(before)))

    # -- Analysis ------------------------------------------------------------

    async def _async_analyze_all(self, timestamp: float) -> None:
        for aquarium_id in list(self._monitors):
            await self._async_analyze(aquarium_id, timestamp)

    async def _async_analyze(self, aquarium_id: str, timestamp: float) -> None:
        """Analyse an aquarium out of the event loop, and publish the result."""
        monitor = self._monitors.get(aquarium_id)
        doc = self._documents.get(aquarium_id)
        if monitor is None or doc is None:
            return
        config = doc["monitoring"]
        if not _configured(config):
            monitor.report = {}
            self._notify(aquarium_id)
            return

        def snapshot(name: str) -> Series | None:
            channel = monitor.channels[name]
            return channel.series.copy() if config.get(f"{name}_entity") else None

        # Windows exclude their end: this one takes in the slot just sampled.
        end = (timestamp // STEP_S + 1) * STEP_S
        report = await self._hass.async_add_executor_job(
            analyze,
            snapshot(CHANNEL_PH),
            snapshot(CHANNEL_ORP),
            snapshot(CHANNEL_CO2),
            end,
            config,
            dict(monitor.alarms),
            dt_util.get_default_time_zone(),
            list(monitor.kh_tests) if config.get("kh_entity") else None,
        )
        monitor.report = report
        # An alarm that cannot be told keeps its last value: it latches.
        monitor.alarms |= {
            key: bool(report["alarms"][key])
            for key in ALARMS
            if report["alarms"][key] is not None
        }
        self._notify(aquarium_id)

    @callback
    def _notify(self, aquarium_id: str) -> None:
        async_dispatcher_send(self._hass, SIGNAL_MONITORING.format(aquarium_id))


def _load_tests(raw: Any) -> dict[str, list[tuple[float, float]]]:
    """Recorded tests read back from the store, bad entries dropped."""
    out: dict[str, list[tuple[float, float]]] = {}
    if not isinstance(raw, dict):
        return out
    for parameter, series in cast(dict[str, Any], raw).items():
        pairs = [
            (float(item[0]), float(item[1]))
            for item in series
            if isinstance(item, (list, tuple))
            and len(item) == 2
            and all(isinstance(x, (int, float)) for x in item)
        ]
        if pairs:
            out[str(parameter)] = sorted(pairs)
    return out


def _in_dkh(attributes: Mapping[str, Any]) -> bool:
    """Whether a state is in dKH: a head dosing calcium gives ppm."""
    unit = attributes.get("unit_of_measurement")
    return unit is None or str(unit).lower() == _KH_UNIT


def _listed_tests(measurements: list[Any]) -> Iterator[KhTest]:
    """The usable KH tests of an entity's history.

    A test flagged as suspect by the entity stays out: comparing with it would
    raise an alarm about the test rather than about the water.
    """
    for raw in measurements:
        if not isinstance(raw, dict) or raw.get("suspect"):
            continue
        item = cast(dict[str, Any], raw)
        at = dt_util.parse_datetime(str(item.get("at")))
        value = item.get("value")
        if at is None or not isinstance(value, int | float):
            continue
        if item.get("parameter", CHANNEL_KH) == CHANNEL_KH:
            yield at.timestamp(), float(value)


def _configured(config: dict[str, Any]) -> bool:
    """Whether an aquarium has something to analyse (CO2 only explains)."""
    return bool(config.get("ph_entity") or config.get("orp_entity"))
