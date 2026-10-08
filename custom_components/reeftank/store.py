"""Persistence of the aquarium documents.

Documents are kept in one HA `Store` (`.storage/reeftank`), so they are part
of the Home Assistant backups. Every save bumps the document's `revision`;
a writer may pass the revision it read to refuse overwriting a newer one
(two tablets editing the same tank).
"""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store

from .const import (
    SIGNAL_AQUARIUM_ADDED,
    SIGNAL_AQUARIUM_UPDATED,
    SIGNAL_AQUARIUMS_CHANGED,
    STORE_KEY,
    STORE_VERSION,
)
from .models import new_id, validate_document

_LOGGER = logging.getLogger(__name__)


class RevisionConflict(Exception):
    """The document was changed since the writer read it."""

    def __init__(self, current: dict[str, Any]) -> None:
        """Keep the current document for the caller to merge with."""
        super().__init__("revision conflict")
        self.current = current


class AquariumStore:
    """All the aquarium documents of the installation."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Create the store; call async_load() before use."""
        self._hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, STORE_VERSION, STORE_KEY)
        self._aquariums: dict[str, dict[str, Any]] = {}

    async def async_load(self) -> None:
        """Read the documents from disk, dropping the ones no longer valid."""
        data = await self._store.async_load() or {}
        for aquarium_id, raw in (data.get("aquariums") or {}).items():
            try:
                doc = validate_document({**raw, "id": aquarium_id})
            except Exception as err:
                # A document the current schema rejects is kept out rather than
                # blocking the whole integration; the raw data stays on disk
                # until the next save of another document.
                _LOGGER.error("Aquarium %s ignored: %s", aquarium_id, err)
                continue
            self._aquariums[aquarium_id] = doc

    @callback
    def _schedule_save(self) -> None:
        self._store.async_delay_save(lambda: {"aquariums": self._aquariums}, 1)

    async def async_flush(self) -> None:
        """Write pending changes now (unload, tests)."""
        await self._store.async_save({"aquariums": self._aquariums})

    # -- Reading -------------------------------------------------------------

    @callback
    def ids(self) -> list[str]:
        """Ids of all the aquariums."""
        return list(self._aquariums)

    @callback
    def get(self, aquarium_id: str) -> dict[str, Any] | None:
        """A copy of one document, or None."""
        doc = self._aquariums.get(aquarium_id)
        return deepcopy(doc) if doc is not None else None

    @callback
    def all(self) -> list[dict[str, Any]]:
        """Copies of all the documents."""
        return [deepcopy(doc) for doc in self._aquariums.values()]

    @callback
    def find(self, ref: str) -> str | None:
        """Resolve an aquarium reference: its id, or its name (any case)."""
        if ref in self._aquariums:
            return ref
        lowered = ref.strip().lower()
        for aquarium_id, doc in self._aquariums.items():
            if doc["name"].lower() == lowered:
                return aquarium_id
        return None

    # -- Writing -------------------------------------------------------------

    @callback
    def save(
        self, data: dict[str, Any], expected_revision: int | None = None
    ) -> dict[str, Any]:
        """Create or replace a document; return the stored copy.

        Raises vol.Invalid for a malformed document and RevisionConflict when
        `expected_revision` is given and is not the current one.
        """
        aquarium_id = data.get("id")
        created = not aquarium_id or aquarium_id not in self._aquariums
        if not aquarium_id:
            aquarium_id = new_id()
        current = self._aquariums.get(aquarium_id)
        if (
            current is not None
            and expected_revision is not None
            and current["revision"] != expected_revision
        ):
            raise RevisionConflict(deepcopy(current))

        doc = validate_document({**data, "id": aquarium_id})
        doc["revision"] = (current["revision"] + 1) if current else 1
        self._aquariums[aquarium_id] = doc
        self._schedule_save()

        if created:
            async_dispatcher_send(self._hass, SIGNAL_AQUARIUM_ADDED, aquarium_id)
        async_dispatcher_send(
            self._hass, SIGNAL_AQUARIUM_UPDATED.format(aquarium_id), deepcopy(doc)
        )
        async_dispatcher_send(self._hass, SIGNAL_AQUARIUMS_CHANGED)
        return deepcopy(doc)

    @callback
    def delete(self, aquarium_id: str) -> bool:
        """Delete a document; return whether it existed."""
        if self._aquariums.pop(aquarium_id, None) is None:
            return False
        self._schedule_save()
        async_dispatcher_send(
            self._hass, SIGNAL_AQUARIUM_UPDATED.format(aquarium_id), None
        )
        async_dispatcher_send(self._hass, SIGNAL_AQUARIUMS_CHANGED)
        return True
