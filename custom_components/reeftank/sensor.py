"""Inventory and feeding counters of every aquarium."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from .const import (
    KEY_CORALS,
    KEY_FEEDINGS_TODAY,
    KEY_FISH,
    SIGNAL_AQUARIUM_ADDED,
    SIGNAL_FEEDING,
)
from .entity import ReefTankEntity
from .models import coral_counts, fish_counts

if TYPE_CHECKING:
    from . import ReefTankConfigEntry, ReefTankData


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
