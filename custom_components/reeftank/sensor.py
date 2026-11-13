"""Inventory and feeding counters of every aquarium."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from .const import (
    CHEMISTRIES,
    KEY_CORALS,
    KEY_FEEDINGS_TODAY,
    KEY_FISH,
    KEY_KH_ESTIMATED,
    KEY_MONITORING,
    KEY_ORP_COMPENSATED,
    KEY_PH_MEAN,
    KEY_PH_SWING,
    KEY_WATER_VOLUME,
    SIGNAL_AQUARIUM_ADDED,
    SIGNAL_FEEDING,
    STATUS_SETTLING,
    STATUSES,
    TEST_DECIMALS,
    TEST_SYMBOLS,
    TEST_UNITS,
)

# Recorded tests shown in a chemistry sensor's history attribute.
from .entity import MonitoringEntity, ReefTankEntity
from .models import coral_counts, fish_counts, placed_devices

if TYPE_CHECKING:
    from . import ReefTankConfigEntry, ReefTankData

_HISTORY_SHOWN = 50


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ReefTankConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the sensors of every aquarium, and of the ones created later."""
    data = entry.runtime_data

    @callback
    def _add(aquarium_id: str) -> None:
        async_add_entities(
            [
                FishSensor(data, aquarium_id),
                CoralSensor(data, aquarium_id),
                FeedingsTodaySensor(data, aquarium_id),
                MonitoringSensor(data, aquarium_id),
                PhMeanSensor(data, aquarium_id),
                PhSwingSensor(data, aquarium_id),
                OrpCompensatedSensor(data, aquarium_id),
                KhEstimatedSensor(data, aquarium_id),
                WaterVolumeSensor(data, aquarium_id),
                *(
                    ChemistrySensor(data, aquarium_id, parameter)
                    for parameter in CHEMISTRIES
                ),
            ]
        )

    for aquarium_id in data.store.ids():
        _add(aquarium_id)
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_AQUARIUM_ADDED, _add))


class _CountSensor(ReefTankEntity, SensorEntity):
    """Number of animals, with the count per species as an attribute."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def _counts(self) -> dict[str, int]:
        raise NotImplementedError

    def _update_from_document(self) -> None:
        """Total count as the state, count per species as attributes."""
        counts = self._counts()
        self._attr_native_value = sum(counts.values())
        self._attr_extra_state_attributes = {
            "species": counts,
            "species_count": len(counts),
        }


class FishSensor(_CountSensor):
    """Number of fish of an aquarium."""

    def __init__(self, data: ReefTankData, aquarium_id: str) -> None:
        """Create the sensor."""
        super().__init__(data, aquarium_id, KEY_FISH)

    def _counts(self) -> dict[str, int]:
        return fish_counts(self._doc)


class CoralSensor(_CountSensor):
    """Number of coral colonies of an aquarium."""

    def __init__(self, data: ReefTankData, aquarium_id: str) -> None:
        """Create the sensor."""
        super().__init__(data, aquarium_id, KEY_CORALS)

    def _counts(self) -> dict[str, int]:
        return coral_counts(self._doc)


class FeedingsTodaySensor(ReefTankEntity, RestoreSensor):
    """Number of feedings since local midnight."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, data: ReefTankData, aquarium_id: str) -> None:
        """Create the sensor at 0."""
        self._count = 0
        self._day = dt_util.now().date().isoformat()
        super().__init__(data, aquarium_id, KEY_FEEDINGS_TODAY)

    async def async_added_to_hass(self) -> None:
        """Restore today's count, follow feedings, reset at midnight."""
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        today = dt_util.now().date().isoformat()
        if last is not None and last.attributes.get("day") == today:
            try:
                self._count = int(float(last.state))
            except (TypeError, ValueError):
                self._count = 0
        self._day = today
        self._update_from_document()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_FEEDING.format(self._aquarium_id), self._on_feeding
            )
        )
        self.async_on_remove(
            async_track_time_change(
                self.hass, self._on_midnight, hour=0, minute=0, second=0
            )
        )

    @callback
    def _on_feeding(self, _event: dict[str, Any]) -> None:
        today = dt_util.now().date().isoformat()
        if today != self._day:
            self._day = today
            self._count = 0
        self._count += 1
        self._update_from_document()
        self.async_write_ha_state()

    @callback
    def _on_midnight(self, _now: Any) -> None:
        self._day = dt_util.now().date().isoformat()
        self._count = 0
        self._update_from_document()
        self.async_write_ha_state()

    def _update_from_document(self) -> None:
        """The count as the state, its day as an attribute (to restore it)."""
        self._attr_native_value = self._count
        self._attr_extra_state_attributes = {"day": self._day}


class MonitoringSensor(MonitoringEntity, SensorEntity):
    """Where the monitoring stands, and how far the learning went."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(STATUSES)

    def __init__(self, data: ReefTankData, aquarium_id: str) -> None:
        """Create the sensor."""
        super().__init__(data, aquarium_id, KEY_MONITORING)

    def _update_from_document(self) -> None:
        """The status as the state, the learning progress as an attribute."""
        monitoring = self._data.monitoring
        self._attr_native_value = monitoring.status(self._aquarium_id)
        learning = monitoring.report(self._aquarium_id).get("learning", 0.0)
        self._attr_extra_state_attributes = {"learning_pct": round(learning * 100)}


class _AnalysisSensor(MonitoringEntity, SensorEntity):
    """A figure of the last analysis, unknown until it can be computed."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _section: str
    _field: str

    def _update_from_document(self) -> None:
        report = self._data.monitoring.report(self._aquarium_id)
        self._attr_native_value = report.get(self._section, {}).get(self._field)


class PhMeanSensor(_AnalysisSensor):
    """Mean pH of the last 24 hours."""

    _attr_suggested_display_precision = 2
    _section = "ph"
    _field = "mean_24h"

    def __init__(self, data: ReefTankData, aquarium_id: str) -> None:
        """Create the sensor."""
        super().__init__(data, aquarium_id, KEY_PH_MEAN)


class PhSwingSensor(_AnalysisSensor):
    """Amplitude of the pH over the last 24 hours."""

    _attr_suggested_display_precision = 2
    _section = "ph"
    _field = "swing_24h"

    def __init__(self, data: ReefTankData, aquarium_id: str) -> None:
        """Create the sensor."""
        super().__init__(data, aquarium_id, KEY_PH_SWING)


class OrpCompensatedSensor(_AnalysisSensor):
    """ORP of the last hour, the daily effect of the pH taken out."""

    _attr_native_unit_of_measurement = "mV"
    _attr_suggested_display_precision = 0
    _section = "orp"
    _field = "compensated"

    def __init__(self, data: ReefTankData, aquarium_id: str) -> None:
        """Create the sensor."""
        super().__init__(data, aquarium_id, KEY_ORP_COMPENSATED)


class KhEstimatedSensor(_AnalysisSensor):
    """KH today, from the last test and what pH and CO2 did since."""

    _attr_native_unit_of_measurement = "dKH"
    _attr_suggested_display_precision = 2
    _section = "kh"
    _field = "estimated"

    def __init__(self, data: ReefTankData, aquarium_id: str) -> None:
        """Create the sensor."""
        super().__init__(data, aquarium_id, KEY_KH_ESTIMATED)

    def _update_from_document(self) -> None:
        """Unknown while a calibration moves the pH under the estimate."""
        super()._update_from_document()
        monitoring = self._data.monitoring
        if monitoring.status(self._aquarium_id) == STATUS_SETTLING:
            self._attr_native_value = None
        kh = monitoring.report(self._aquarium_id).get("kh", {})
        self._attr_extra_state_attributes = {"last_test": kh.get("last")}


class WaterVolumeSensor(ReefTankEntity, SensorEntity):
    """Net water volume of an aquarium (L), unknown until set.

    The attributes tell other integrations which aquarium this is: its
    vendor cloud aquarium and the devices placed on its views. The redsea
    integration finds the volume of a ReefDose's tank this way, without
    depending on reeftank.
    """

    _attr_device_class = SensorDeviceClass.VOLUME_STORAGE
    _attr_native_unit_of_measurement = UnitOfVolume.LITERS
    _attr_suggested_display_precision = 0

    def __init__(self, data: ReefTankData, aquarium_id: str) -> None:
        """Create the sensor."""
        super().__init__(data, aquarium_id, KEY_WATER_VOLUME)

    def _update_from_document(self) -> None:
        """The volume as the state, the aquarium's links as attributes."""
        self._attr_native_value = self._doc.get("water_volume_l")
        self._attr_extra_state_attributes = {
            "cloud": self._doc.get("cloud"),
            "device_ids": placed_devices(self._doc),
        }


class ChemistrySensor(MonitoringEntity, SensorEntity):
    """Last hand-entered test of one chemistry: the aquarium's own value.

    Like WaterVolumeSensor, it carries the aquarium's cloud link and placed
    devices as attributes, so the redsea integration reads a ReefDose head's
    chemistry here (by the ``_<parameter>`` id suffix) without depending on
    reeftank. The ``measurements`` attribute is the recent history, in the
    shape the monitoring and the card already read.
    """

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, data: ReefTankData, aquarium_id: str, parameter: str) -> None:
        """Create the sensor of one chemistry."""
        self._parameter = parameter
        self._attr_native_unit_of_measurement = TEST_UNITS[parameter]
        self._attr_suggested_display_precision = TEST_DECIMALS[parameter]
        super().__init__(data, aquarium_id, parameter)
        # A universal symbol as the name: no per-locale translation needed.
        self._attr_translation_key = None
        self._attr_name = TEST_SYMBOLS[parameter]

    def _update_from_document(self) -> None:
        """Last test value as the state, history and links as attributes."""
        monitoring = self._data.monitoring
        last = monitoring.last_test(self._aquarium_id, self._parameter)
        history = monitoring.tests_of(self._aquarium_id, self._parameter)
        self._attr_native_value = last[1] if last is not None else None
        self._attr_extra_state_attributes = {
            # Marks the sensor to readers (redsea, the card) unambiguously,
            # whatever the entity id a short chemistry key (i, k) ends up with.
            "reef_parameter": self._parameter,
            # The aquarium a recorded test is filed against (the water_test
            # service resolves it).
            "aquarium": self._aquarium_id,
            "cloud": self._doc.get("cloud"),
            "device_ids": placed_devices(self._doc),
            "tested_at": (
                dt_util.utc_from_timestamp(last[0]).isoformat()
                if last is not None
                else None
            ),
            "measurements": [
                {
                    "at": dt_util.utc_from_timestamp(at).isoformat(),
                    "value": value,
                    "parameter": self._parameter,
                }
                for at, value in history[-_HISTORY_SHOWN:]
            ],
        }
