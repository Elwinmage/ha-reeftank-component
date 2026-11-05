"""Alarms of every aquarium: what differs from what is usual for this tank."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.binary_sensor.const import BinarySensorDeviceClass
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    KEY_KH_FAST_CHANGE,
    KEY_ORP_LOW,
    KEY_PH_BASE_LOW,
    KEY_PH_PROFILE_OFF,
    KEY_PH_SWING_HIGH,
    KEY_PROBE_SUSPECT,
    SIGNAL_AQUARIUM_ADDED,
)
from .entity import MonitoringEntity

if TYPE_CHECKING:
    from . import ReefTankConfigEntry, ReefTankData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ReefTankConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the alarms of every aquarium, and of the ones created later."""
    data = entry.runtime_data

    @callback
    def _add(aquarium_id: str) -> None:
        async_add_entities(
            [
                PhBaseAlarm(data, aquarium_id),
                PhSwingAlarm(data, aquarium_id),
                PhProfileAlarm(data, aquarium_id),
                OrpAlarm(data, aquarium_id),
                ProbeAlarm(data, aquarium_id),
                KhAlarm(data, aquarium_id),
            ]
        )

    for aquarium_id in data.store.ids():
        _add(aquarium_id)
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_AQUARIUM_ADDED, _add))


class _Alarm(MonitoringEntity, BinarySensorEntity):
    """An alarm: unknown while it cannot be told."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _alarm: str

    def _details(self) -> dict[str, object]:
        raise NotImplementedError

    def _update_from_document(self) -> None:
        """Read the alarm and what explains it from the last analysis."""
        monitoring = self._data.monitoring
        self._attr_is_on = monitoring.alarm(self._aquarium_id, self._alarm)
        self._attr_extra_state_attributes = self._details()


class PhBaseAlarm(_Alarm):
    """The pH of the last 24 hours is below its usual level."""

    _alarm = KEY_PH_BASE_LOW

    def __init__(self, data: ReefTankData, aquarium_id: str) -> None:
        """Create the alarm."""
        super().__init__(data, aquarium_id, KEY_PH_BASE_LOW)

    def _details(self) -> dict[str, object]:
        ph = self._data.monitoring.report(self._aquarium_id).get("ph", {})
        return {
            key: ph.get(key)
            for key in (
                "baseline",
                "drop",
                "cause",
                "co2_explained_drop",
                "kh_explained_drop",
                "kh_test_due",
            )
            if key in ph
        }


class PhSwingAlarm(_Alarm):
    """The pH moved more than usual over the last 24 hours."""

    _alarm = KEY_PH_SWING_HIGH

    def __init__(self, data: ReefTankData, aquarium_id: str) -> None:
        """Create the alarm."""
        super().__init__(data, aquarium_id, KEY_PH_SWING_HIGH)

    def _details(self) -> dict[str, object]:
        ph = self._data.monitoring.report(self._aquarium_id).get("ph", {})
        return {key: ph[key] for key in ("swing_baseline",) if key in ph}


class PhProfileAlarm(_Alarm):
    """The pH of the last hours does not follow the usual day."""

    _alarm = KEY_PH_PROFILE_OFF

    def __init__(self, data: ReefTankData, aquarium_id: str) -> None:
        """Create the alarm."""
        super().__init__(data, aquarium_id, KEY_PH_PROFILE_OFF)

    def _details(self) -> dict[str, object]:
        ph = self._data.monitoring.report(self._aquarium_id).get("ph", {})
        return {key: ph[key] for key in ("profile_hours_off",) if key in ph}


class OrpAlarm(_Alarm):
    """ORP, the pH effect taken out, stays below its usual level."""

    _alarm = KEY_ORP_LOW

    def __init__(self, data: ReefTankData, aquarium_id: str) -> None:
        """Create the alarm."""
        super().__init__(data, aquarium_id, KEY_ORP_LOW)

    def _details(self) -> dict[str, object]:
        orp = self._data.monitoring.report(self._aquarium_id).get("orp", {})
        return {
            key: orp[key]
            for key in ("baseline", "drop", "ph_slope", "ph_correlation")
            if key in orp
        }


class ProbeAlarm(_Alarm):
    """A probe reads something no water would do."""

    _alarm = KEY_PROBE_SUSPECT

    def __init__(self, data: ReefTankData, aquarium_id: str) -> None:
        """Create the alarm."""
        super().__init__(data, aquarium_id, KEY_PROBE_SUSPECT)

    def _details(self) -> dict[str, object]:
        report = self._data.monitoring.report(self._aquarium_id)
        return {"probes": report.get("probes", {})}


class KhAlarm(_Alarm):
    """The KH moved too much between the last two tests."""

    _alarm = KEY_KH_FAST_CHANGE

    def __init__(self, data: ReefTankData, aquarium_id: str) -> None:
        """Create the alarm."""
        super().__init__(data, aquarium_id, KEY_KH_FAST_CHANGE)

    def _details(self) -> dict[str, object]:
        kh = self._data.monitoring.report(self._aquarium_id).get("kh", {})
        return {key: kh[key] for key in ("last", "change") if key in kh}
