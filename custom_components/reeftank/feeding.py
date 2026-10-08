"""Feeding events: watch the feeding sources of every aquarium.

A feeding source is an entity whose change means "food was dropped": the
last-feed sensor of a feeder, a feeding switch (the ReefBeat feeding
shortcut), a button... Triggers are handled here, server side, so a feeding
is recorded even when no card is open.

Triggers closer than `dedup_s` are merged: a feeder and the feeding shortcut
it starts fire together, but it is one feeding.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from homeassistant.const import STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import (
    FEED_FEEDER,
    FEED_MANUAL,
    FEED_SHORTCUT,
    SIGNAL_AQUARIUM_UPDATED,
    SIGNAL_FEEDING,
)

if TYPE_CHECKING:
    from .store import AquariumStore

_LOGGER = logging.getLogger(__name__)

# Domains whose entities trigger when they turn on, rather than on any change.
_SWITCH_DOMAINS = ("switch", "input_boolean", "binary_sensor", "light", "fan")
_INVALID = (None, STATE_UNAVAILABLE, STATE_UNKNOWN)


def default_kind(entity_id: str) -> str:
    """The kind of feeding a source stands for, when it does not say."""
    domain = entity_id.split(".", 1)[0]
    return FEED_SHORTCUT if domain in _SWITCH_DOMAINS else FEED_FEEDER


def is_trigger(entity_id: str, old: str | None, new: str | None) -> bool:
    """Whether a state change of a feeding source means a feeding.

    Changes from or to an unknown state are ignored: an entity coming back
    after a restart is not a feeding.
    """
    if old in _INVALID or new in _INVALID or old == new:
        return False
    if entity_id.split(".", 1)[0] in _SWITCH_DOMAINS:
        return new == STATE_ON
    return True


class FeedingManager:
    """Feeding sources of all the aquariums."""

    def __init__(self, hass: HomeAssistant, store: AquariumStore) -> None:
        """Create the manager; call async_start() to begin watching."""
        self._hass = hass
        self._store = store
        self._tracks: dict[str, Callable[[], None]] = {}
        self._doc_listeners: dict[str, Callable[[], None]] = {}
        self._last: dict[str, float] = {}

    @callback
    def async_start(self) -> None:
        """Watch the sources of every aquarium."""
        for aquarium_id in self._store.ids():
            self.async_watch(aquarium_id)

    @callback
    def async_stop(self) -> None:
        """Stop watching everything."""
        for unsub in [*self._tracks.values(), *self._doc_listeners.values()]:
            unsub()
        self._tracks.clear()
        self._doc_listeners.clear()

    @callback
    def async_watch(self, aquarium_id: str) -> None:
        """Watch an aquarium: its sources now, and again whenever it changes."""
        if aquarium_id not in self._doc_listeners:

            @callback
            def _updated(doc: dict[str, Any] | None) -> None:
                self._retrack(aquarium_id, doc)

            self._doc_listeners[aquarium_id] = async_dispatcher_connect(
                self._hass, SIGNAL_AQUARIUM_UPDATED.format(aquarium_id), _updated
            )
        self._retrack(aquarium_id, self._store.get(aquarium_id))

    @callback
    def _retrack(self, aquarium_id: str, doc: dict[str, Any] | None) -> None:
        if unsub := self._tracks.pop(aquarium_id, None):
            unsub()
        if doc is None:
            # Deleted: forget it entirely.
            if unsub_doc := self._doc_listeners.pop(aquarium_id, None):
                unsub_doc()
            self._last.pop(aquarium_id, None)
            return
        sources = {s["entity_id"]: s for s in doc["feeding"]["sources"]}
        if not sources:
            return

        @callback
        def _changed(event: Event[EventStateChangedData]) -> None:
            entity_id = event.data["entity_id"]
            old = event.data["old_state"]
            new = event.data["new_state"]
            if not is_trigger(
                entity_id,
                old.state if old else None,
                new.state if new else None,
            ):
                return
            # Only the source entities are tracked.
            source = sources[entity_id]
            self.async_feed(
                aquarium_id,
                source.get("kind") or default_kind(entity_id),
                source["id"],
            )

        self._tracks[aquarium_id] = async_track_state_change_event(
            self._hass, list(sources), _changed
        )

    @callback
    def async_feed(
        self, aquarium_id: str, kind: str = FEED_MANUAL, source: str | None = None
    ) -> bool:
        """Record a feeding; return False when merged with a recent one."""
        doc = self._store.get(aquarium_id)
        if doc is None:
            return False
        now = dt_util.utcnow().timestamp()
        last = self._last.get(aquarium_id)
        if last is not None and now - last < doc["feeding"]["dedup_s"]:
            _LOGGER.debug("Feeding of %s merged with the previous one", aquarium_id)
            return False
        self._last[aquarium_id] = now
        if kind not in (FEED_FEEDER, FEED_SHORTCUT, FEED_MANUAL):
            kind = FEED_MANUAL
        async_dispatcher_send(
            self._hass,
            SIGNAL_FEEDING.format(aquarium_id),
            {"kind": kind, "source": source},
        )
        return True
