"""ReefTank integration.

Backs the aquarium view of ha-reef-card: stores the aquarium documents and
their pictures, serves the asset catalog, records feedings and exposes the
inventory as entities. See README.md for the architecture.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .compat import StaticPathConfig, find_device, vol
from .const import (
    CATALOG_DEVICE_ID,
    DATA_DIR,
    DOMAIN,
    IMAGES_DIR,
    KEY_CORALS,
    KEY_FEEDING,
    KEY_FEEDINGS_TODAY,
    KEY_FISH,
    PACK_DIR,
    PLATFORMS,
    URL_CATALOG_PACK,
    URL_CATALOG_USER,
    URL_IMAGES,
    USER_CATALOG_DIR,
)
from .feeding import FeedingManager
from .images import ImageUploadView, cleanup_orphans, delete_aquarium_images
from .models import referenced_images
from .services import async_register_services
from .store import AquariumStore
from .updater import CatalogUpdater
from .websocket import async_register_websocket

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

# Static paths and views cannot be unregistered: they are added once per
# Home Assistant run, and look up the current runtime data when used.
_HTTP_REGISTERED = f"{DOMAIN}_http_registered"


@dataclass
class ReefTankData:
    """Runtime data of the integration."""

    hass: HomeAssistant
    store: AquariumStore
    images_root: Path
    user_catalog_root: Path
    pack_root: Path
    updater: CatalogUpdater
    feeding: FeedingManager = field(init=False)

    def __post_init__(self) -> None:
        """Create the feeding manager over the store."""
        self.feeding = FeedingManager(self.hass, self.store)

    async def async_save(
        self, data: dict[str, Any], expected_revision: int | None = None
    ) -> dict[str, Any]:
        """Save a document, then keep its device and pictures in step."""
        doc = self.store.save(data, expected_revision)
        self.feeding.async_watch(doc["id"])

        dev_reg = dr.async_get(self.hass)
        device = find_device(dev_reg, (DOMAIN, doc["id"]))
        if device is not None and device.name != doc["name"]:
            dev_reg.async_update_device(device.id, name=doc["name"])

        await self.hass.async_add_executor_job(
            cleanup_orphans, self.images_root, doc["id"], referenced_images(doc)
        )
        return doc

    async def async_delete(self, aquarium_id: str, remove_device: bool = True) -> bool:
        """Delete a document, its device, entities and pictures."""
        if not self.store.delete(aquarium_id):
            return False
        if remove_device:
            dev_reg = dr.async_get(self.hass)
            device = find_device(dev_reg, (DOMAIN, aquarium_id))
            if device is not None:
                dev_reg.async_remove_device(device.id)
        await self.hass.async_add_executor_job(
            delete_aquarium_images, self.images_root, aquarium_id
        )
        return True

    def entity_ids(self, aquarium_id: str) -> dict[str, str | None]:
        """Entity ids of an aquarium's entities, by key."""
        ent_reg = er.async_get(self.hass)
        wanted = {
            KEY_FISH: "sensor",
            KEY_CORALS: "sensor",
            KEY_FEEDINGS_TODAY: "sensor",
            KEY_FEEDING: "event",
        }
        return {
            key: ent_reg.async_get_entity_id(platform, DOMAIN, f"{aquarium_id}_{key}")
            for key, platform in wanted.items()
        }


type ReefTankConfigEntry = ConfigEntry[ReefTankData]


def get_data(hass: HomeAssistant) -> ReefTankData:
    """Runtime data of the loaded config entry.

    Raises vol.Invalid when the integration is not set up.
    """
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        return entry.runtime_data
    raise vol.Invalid("reeftank is not set up")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the WebSocket commands and the services."""
    async_register_websocket(hass)
    async_register_services(hass)
    return True


def _make_dirs(*paths: Path) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


async def _async_register_http(hass: HomeAssistant, data: ReefTankData) -> None:
    """Serve the pictures and the catalogs, accept uploads (once per run)."""
    if hass.data.get(_HTTP_REGISTERED):
        hass.data[_HTTP_REGISTERED].current = data
        return
    if not hass.http:  # pragma: no cover - http is a dependency
        return

    holder = _DataHolder(data)
    hass.data[_HTTP_REGISTERED] = holder
    await hass.http.async_register_static_paths(
        [
            # Picture names are random and never rewritten: cacheable.
            StaticPathConfig(URL_IMAGES, str(data.images_root), cache_headers=True),
            # The pack folder is replaced by updates, the path stays
            StaticPathConfig(
                URL_CATALOG_PACK, str(data.pack_root), cache_headers=False
            ),
            StaticPathConfig(
                URL_CATALOG_USER, str(data.user_catalog_root), cache_headers=False
            ),
        ]
    )
    hass.http.register_view(ImageUploadView(holder))


class _DataHolder:
    """Indirection letting the upload view follow config entry reloads."""

    def __init__(self, data: ReefTankData) -> None:
        self.current = data

    @property
    def images_root(self) -> Path:
        return self.current.images_root


async def async_setup_entry(hass: HomeAssistant, entry: ReefTankConfigEntry) -> bool:
    """Load the documents, start the feeding watch, add the entities."""
    store = AquariumStore(hass)
    await store.async_load()

    images_root = Path(hass.config.path(DATA_DIR, IMAGES_DIR))
    user_catalog_root = Path(hass.config.path(DATA_DIR, USER_CATALOG_DIR))
    pack_root = Path(hass.config.path(DATA_DIR, PACK_DIR))
    await hass.async_add_executor_job(
        _make_dirs, images_root, user_catalog_root, pack_root
    )

    integration = await async_get_integration(hass, DOMAIN)
    updater = CatalogUpdater(hass, entry, pack_root, str(integration.version or "0"))
    data = ReefTankData(hass, store, images_root, user_catalog_root, pack_root, updater)
    entry.runtime_data = data

    await _async_register_http(hass, data)
    await updater.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    data.feeding.async_start()
    entry.async_on_unload(data.feeding.async_stop)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def _async_options_updated(
    hass: HomeAssistant, entry: ReefTankConfigEntry
) -> None:
    """Automatic updates turned on: check right away."""
    updater = entry.runtime_data.updater
    if updater.auto_update:
        await updater.coordinator.async_refresh()


async def async_unload_entry(hass: HomeAssistant, entry: ReefTankConfigEntry) -> bool:
    """Unload the platforms and write pending changes."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.store.async_flush()
    return unloaded


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: ReefTankConfigEntry, device: dr.DeviceEntry
) -> bool:
    """Deleting an aquarium's device from the UI deletes the aquarium.

    The catalog's device stays: it carries the update entity.
    """
    if (DOMAIN, CATALOG_DEVICE_ID) in device.identifiers:
        return False
    for domain, aquarium_id in device.identifiers:
        if domain == DOMAIN:
            # Home Assistant removes the device itself once this returns.
            await entry.runtime_data.async_delete(aquarium_id, remove_device=False)
    return True
