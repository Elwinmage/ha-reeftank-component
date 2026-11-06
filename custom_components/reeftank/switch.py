"""Pause of the monitoring of an aquarium (cleaning a probe, a water change)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import KEY_MONITORING_PAUSE, SIGNAL_AQUARIUM_ADDED
from .entity import MonitoringEntity

if TYPE_CHECKING:
    from . import ReefTankConfigEntry, ReefTankData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ReefTankConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the pause of every aquarium, and of the ones created later."""
    data = entry.runtime_data

    @callback
    def _add(aquarium_id: str) -> None:
        async_add_entities([MonitoringPauseSwitch(data, aquarium_id)])

    for aquarium_id in data.store.ids():
        _add(aquarium_id)
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_AQUARIUM_ADDED, _add))


class MonitoringPauseSwitch(MonitoringEntity, SwitchEntity):
    """On while the analysis is suspended; turns off by itself."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, data: ReefTankData, aquarium_id: str) -> None:
        """Create the switch."""
        super().__init__(data, aquarium_id, KEY_MONITORING_PAUSE)

    def _update_from_document(self) -> None:
        """On until the end of the pause, given as an attribute."""
        until = self._data.monitoring.user_paused_until(self._aquarium_id)
        self._attr_is_on = until is not None
        self._attr_extra_state_attributes = {
            "until": until.isoformat() if until else None
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Pause, for the time set in the aquarium."""
        self._data.monitoring.async_pause(self._aquarium_id, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Resume now."""
        self._data.monitoring.async_pause(self._aquarium_id, False)
