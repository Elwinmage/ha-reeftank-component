"""Base entity: one device per aquarium."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, MANUFACTURER, MODEL, SIGNAL_AQUARIUM_UPDATED

if TYPE_CHECKING:
    from . import ReefTankData


class ReefTankEntity(Entity):
    """An entity of an aquarium, refreshed whenever its document changes."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, data: ReefTankData, aquarium_id: str, key: str) -> None:
        """Bind the entity to its aquarium."""
        self._data = data
        self._aquarium_id = aquarium_id
        self._doc: dict[str, Any] = data.store.get(aquarium_id) or {}
        self._attr_unique_id = f"{aquarium_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, aquarium_id)},
            name=self._doc.get("name") or aquarium_id,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )
        self._update_from_document()

    async def async_added_to_hass(self) -> None:
        """Follow the changes of the aquarium document."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_AQUARIUM_UPDATED.format(self._aquarium_id),
                self._on_document,
            )
        )

    @callback
    def _on_document(self, doc: dict[str, Any] | None) -> None:
        if doc is None:
            # Deleted: the device registry removes the entity.
            return
        self._doc = doc
        self._update_from_document()
        self.async_write_ha_state()

    def _update_from_document(self) -> None:
        """Refresh the `_attr_*` values derived from the document."""
