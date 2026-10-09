"""Keeps the downloaded catalog (pack) up to date.

Checks the latest release of the catalog repository every 12 hours and,
unless the user turned it off in the options, installs it right away. The
update entity shows the state and installs on demand.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CATALOG_CHECK_HOURS,
    CATALOG_REPO,
    CONF_AUTO_UPDATE,
    DEFAULT_AUTO_UPDATE,
    DOMAIN,
    SIGNAL_CATALOG_UPDATED,
)
from .pack import (
    Manifest,
    PackClient,
    PackError,
    commit,
    extract_entry,
    is_compatible,
    plan,
    prepare_staging,
    read_installed,
)

_LOGGER = logging.getLogger(__name__)


class CatalogUpdater:
    """State of the pack, its checks and its installs."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        root: Path,
        integration_version: str,
        repo: str = CATALOG_REPO,
    ) -> None:
        """Bind to the pack folder."""
        self.hass = hass
        self.entry = entry
        self.root = root
        self.integration_version = integration_version
        self.client = PackClient(async_get_clientsession(hass), repo)
        self.installed: Manifest | None = None
        self.latest: Manifest | None = None
        self.in_progress = False
        self.progress: int | None = None
        self.coordinator: DataUpdateCoordinator[Manifest] = DataUpdateCoordinator(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} catalog",
            update_interval=timedelta(hours=CATALOG_CHECK_HOURS),
            update_method=self._async_check,
        )
        self._listeners: list[Callable[[], None]] = []

    # -- state ----------------------------------------------------------------

    @property
    def auto_update(self) -> bool:
        """Install new releases without asking."""
        return bool(self.entry.options.get(CONF_AUTO_UPDATE, DEFAULT_AUTO_UPDATE))

    @property
    def compatible(self) -> bool:
        """The latest release can be used by this integration."""
        return self.latest is None or is_compatible(
            self.latest, self.integration_version
        )

    @property
    def update_available(self) -> bool:
        """A release newer than the installed pack (or no pack at all)."""
        if self.latest is None:
            return False
        if self.installed is None:
            return True
        return self.latest.raw != self.installed.raw

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> CALLBACK_TYPE:
        """Be told when the state changes (progress, install done)."""
        self._listeners.append(listener)

        @callback
        def _remove() -> None:
            self._listeners.remove(listener)

        return _remove

    @callback
    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()

    # -- checks ---------------------------------------------------------------

    async def async_start(self) -> None:
        """Read the installed pack, then check for a release (not blocking)."""
        self.installed = await self.hass.async_add_executor_job(
            read_installed, self.root
        )
        # A first check that fails (offline) must not fail the setup
        await self.coordinator.async_refresh()

    async def _async_check(self) -> Manifest:
        try:
            latest = await self.client.latest()
        except PackError as err:
            raise UpdateFailed(f"catalog check failed: {err}") from err
        self.latest = latest
        if self.auto_update and self.update_available and not self.in_progress:
            if self.compatible:
                self.entry.async_create_background_task(
                    self.hass, self._async_auto_install(), f"{DOMAIN} catalog install"
                )
            else:
                _LOGGER.warning(
                    "Catalog %s needs ReefTank %s or newer: not installed",
                    latest.version,
                    latest.min_integration,
                )
        return latest

    async def _async_auto_install(self) -> None:
        try:
            await self.async_install()
        except HomeAssistantError as err:
            _LOGGER.warning("Catalog update failed: %s", err)

    # -- install --------------------------------------------------------------

    async def async_install(self) -> None:
        """Install the latest release. Raises HomeAssistantError."""
        latest = self.latest
        if latest is None:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="catalog_unknown"
            )
        if not is_compatible(latest, self.integration_version):
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="catalog_incompatible",
                translation_placeholders={
                    "version": latest.version,
                    "minimum": str(latest.min_integration),
                },
            )
        if self.in_progress:
            return
        self.in_progress = True
        self.progress = 0
        self._notify()
        try:
            installed = await self.hass.async_add_executor_job(
                read_installed, self.root
            )
            keep, fetch = plan(installed, latest)
            staging = await self.hass.async_add_executor_job(
                prepare_staging, self.root, keep
            )
            for done, item in enumerate(fetch, start=1):
                blob = await self.client.entry(latest, item)
                await self.hass.async_add_executor_job(
                    extract_entry, blob, item.kind, staging / item.kind / item.entry_id
                )
                self.progress = round(100 * done / len(fetch))
                self._notify()
            await self.hass.async_add_executor_job(commit, self.root, staging, latest)
        except (PackError, OSError) as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="catalog_install_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        finally:
            self.in_progress = False
            self.progress = None
            self._notify()
        self.installed = latest
        _LOGGER.info(
            "Catalog %s installed (%d entries downloaded, %d kept)",
            latest.version,
            len(fetch),
            len(keep),
        )
        async_dispatcher_send(self.hass, SIGNAL_CATALOG_UPDATED, latest.version)
        self._notify()
