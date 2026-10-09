"""Update entity of the downloaded catalog (fish and coral species)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CATALOG_DEVICE_ID, DOMAIN, MANUFACTURER

if TYPE_CHECKING:
    from . import ReefTankConfigEntry
    from .pack import Manifest
    from .updater import CatalogUpdater

#: Version shown while no pack is installed
NOT_INSTALLED = "0"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ReefTankConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the catalog update entity."""
    async_add_entities([CatalogUpdateEntity(entry.runtime_data.updater)])


class CatalogUpdateEntity(UpdateEntity):
    """Installed and latest catalog release; installs on demand."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    # Named after its device: update.reeftank_catalog
    _attr_name = None
    _attr_unique_id = "catalog"
    _attr_title = "ReefTank catalog"
    _attr_supported_features = (
        UpdateEntityFeature.INSTALL
        | UpdateEntityFeature.PROGRESS
        | UpdateEntityFeature.RELEASE_NOTES
    )

    def __init__(self, updater: CatalogUpdater) -> None:
        """Bind to the updater."""
        self._updater = updater
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, CATALOG_DEVICE_ID)},
            name="ReefTank catalog",
            manufacturer=MANUFACTURER,
            entry_type=DeviceEntryType.SERVICE,
        )
        # Available even when GitHub is not: the installed pack is known
        self._refresh()

    async def async_added_to_hass(self) -> None:
        """Follow the checks and the installs."""
        self.async_on_remove(
            self._updater.coordinator.async_add_listener(self._on_change)
        )
        self.async_on_remove(self._updater.async_add_listener(self._on_change))

    @callback
    def _on_change(self) -> None:
        self._refresh()
        self.async_write_ha_state()

    def _refresh(self) -> None:
        """Copy the updater state into the entity attributes."""
        updater = self._updater
        installed = updater.installed
        latest: Manifest | None = updater.latest
        self._attr_installed_version = installed.version if installed else NOT_INSTALLED
        self._attr_latest_version = (
            latest.version
            if latest is not None and updater.update_available
            else self._attr_installed_version
        )
        self._attr_release_url = (
            updater.client.release_url(latest.version) if latest else None
        )
        self._attr_release_summary = (
            f"Needs ReefTank {latest.min_integration} or newer."
            if latest is not None and not updater.compatible
            else None
        )
        self._attr_in_progress = updater.in_progress
        self._attr_update_percentage = updater.progress

    async def async_release_notes(self) -> str | None:
        """Notes of the latest release."""
        latest = self._updater.latest
        return latest.notes if latest and latest.notes else None

    async def async_install(
        self, version: str | None, backup: bool, **kwargs: Any
    ) -> None:
        """Install the latest release."""
        await self._updater.async_install()
