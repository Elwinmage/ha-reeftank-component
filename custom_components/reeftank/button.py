"""Button of the catalog device: check for a new catalog release now."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CATALOG_DEVICE_ID, DOMAIN, MANUFACTURER

if TYPE_CHECKING:
    from . import ReefTankConfigEntry
    from .updater import CatalogUpdater


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ReefTankConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the catalog check button."""
    async_add_entities([CatalogCheckButton(entry.runtime_data.updater)])


class CatalogCheckButton(ButtonEntity):
    """Check the catalog repository for a release, without waiting 12 h.

    A release found is installed right away when automatic updates are on;
    otherwise the update entity offers it.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "check_catalog"
    _attr_unique_id = "catalog_check"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, updater: CatalogUpdater) -> None:
        """Bind to the updater, on the catalog device."""
        self._updater = updater
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, CATALOG_DEVICE_ID)},
            name="ReefTank catalog",
            manufacturer=MANUFACTURER,
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_press(self) -> None:
        """Check now. Raises HomeAssistantError when the check fails."""
        coordinator = self._updater.coordinator
        await coordinator.async_refresh()
        if not coordinator.last_update_success:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="catalog_check_failed",
                translation_placeholders={
                    "error": str(coordinator.last_exception or "")
                },
            )
