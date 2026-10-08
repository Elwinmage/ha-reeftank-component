"""Feeding event of every aquarium: its state is the time of the last one."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    FEED_KINDS,
    KEY_FEEDING,
    SIGNAL_AQUARIUM_ADDED,
    SIGNAL_FEEDING,
)
from .entity import ReefTankEntity

if TYPE_CHECKING:
    from . import ReefTankConfigEntry, ReefTankData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ReefTankConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the feeding event of every aquarium, and of the ones created later."""
    data = entry.runtime_data

    @callback
    def _add(aquarium_id: str) -> None:
        async_add_entities([FeedingEvent(data, aquarium_id)])

    for aquarium_id in data.store.ids():
        _add(aquarium_id)
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_AQUARIUM_ADDED, _add))


class FeedingEvent(ReefTankEntity, EventEntity):
    """Fired on every feeding; the card animates the fish from it."""

    _attr_event_types = list(FEED_KINDS)

    def __init__(self, data: ReefTankData, aquarium_id: str) -> None:
        """Create the event entity."""
        super().__init__(data, aquarium_id, KEY_FEEDING)

    async def async_added_to_hass(self) -> None:
        """Follow the feedings of the aquarium."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_FEEDING.format(self._aquarium_id), self._on_feeding
            )
        )

    @callback
    def _on_feeding(self, event: dict[str, Any]) -> None:
        self._trigger_event(event["kind"], {"source": event.get("source")})
        self.async_write_ha_state()
