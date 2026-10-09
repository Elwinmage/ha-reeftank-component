"""Services: feeding and inventory changes from automations or scripts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.util import dt as dt_util

from .compat import vol
from .const import (
    ATTR_AQUARIUM,
    ATTR_COUNT,
    ATTR_LINE_ID,
    ATTR_NOTE,
    ATTR_SIZE_CM,
    ATTR_SOURCE,
    ATTR_SPECIES,
    ATTR_WATER,
    DOMAIN,
    FEED_MANUAL,
    SERVICE_FEED,
    SERVICE_LIVESTOCK_ADD,
    SERVICE_LIVESTOCK_REMOVE,
)
from .feeding import default_kind
from .models import LIVESTOCK_KINDS, livestock_add, livestock_remove

if TYPE_CHECKING:
    from . import ReefTankData

FEED_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_AQUARIUM): cv.string,
        vol.Optional(ATTR_SOURCE): cv.string,
    }
)

ADD_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_AQUARIUM): cv.string,
        vol.Optional(ATTR_WATER, default="main"): cv.string,
        vol.Required(ATTR_SPECIES): cv.string,
        vol.Optional(ATTR_COUNT, default=1): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=10000)
        ),
        vol.Optional("kind", default="fish"): vol.In(LIVESTOCK_KINDS),
        vol.Optional(ATTR_SIZE_CM): vol.All(
            [vol.Coerce(float)], vol.Length(min=2, max=2)
        ),
        vol.Optional(ATTR_NOTE): cv.string,
    }
)

REMOVE_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(ATTR_AQUARIUM): cv.string,
            vol.Optional(ATTR_LINE_ID): cv.string,
            vol.Optional(ATTR_SPECIES): cv.string,
            vol.Optional(ATTR_COUNT, default=1): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=10000)
            ),
        }
    ),
    cv.has_at_least_one_key(ATTR_LINE_ID, ATTR_SPECIES),
)


def _runtime(hass: HomeAssistant) -> ReefTankData:
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        return entry.runtime_data
    raise ServiceValidationError(
        translation_domain=DOMAIN, translation_key="not_loaded"
    )


def _resolve(hass: HomeAssistant, data: ReefTankData, ref: str) -> str:
    """An aquarium id from its id, its name, or its device id."""
    if aquarium_id := data.store.find(ref):
        return aquarium_id
    device = dr.async_get(hass).async_get(ref)
    if device is not None:
        for domain, ident in device.identifiers:
            if domain == DOMAIN and data.store.get(ident) is not None:
                return ident
    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="unknown_aquarium",
        translation_placeholders={"aquarium": ref},
    )


@callback
def async_register_services(hass: HomeAssistant) -> None:
    """Register the services (once, at integration setup)."""

    async def handle_feed(call: ServiceCall) -> None:
        data = _runtime(hass)
        aquarium_id = _resolve(hass, data, call.data[ATTR_AQUARIUM])
        doc = data.store.get(aquarium_id) or {}
        source_id = call.data.get(ATTR_SOURCE)
        kind = FEED_MANUAL
        if source_id:
            sources = {s["id"]: s for s in doc.get("feeding", {}).get("sources", [])}
            source = sources.get(source_id)
            if source is None:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="unknown_source",
                    translation_placeholders={"source": source_id},
                )
            kind = source.get("kind") or default_kind(source["entity_id"])
        data.feeding.async_feed(aquarium_id, kind, source_id)

    async def handle_add(call: ServiceCall) -> None:
        data = _runtime(hass)
        aquarium_id = _resolve(hass, data, call.data[ATTR_AQUARIUM])
        doc: dict[str, Any] = data.store.get(aquarium_id) or {}
        livestock_add(
            doc,
            call.data[ATTR_WATER],
            call.data[ATTR_SPECIES],
            call.data[ATTR_COUNT],
            kind=call.data["kind"],
            size_cm=call.data.get(ATTR_SIZE_CM),
            note=call.data.get(ATTR_NOTE),
            added=dt_util.now().date().isoformat(),
        )
        await data.async_save(doc)

    async def handle_remove(call: ServiceCall) -> None:
        data = _runtime(hass)
        aquarium_id = _resolve(hass, data, call.data[ATTR_AQUARIUM])
        doc: dict[str, Any] = data.store.get(aquarium_id) or {}
        try:
            livestock_remove(
                doc,
                call.data[ATTR_COUNT],
                line_id=call.data.get(ATTR_LINE_ID),
                species=call.data.get(ATTR_SPECIES),
            )
        except KeyError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_line",
                translation_placeholders={
                    "line": str(
                        call.data.get(ATTR_LINE_ID) or call.data.get(ATTR_SPECIES)
                    )
                },
            ) from err
        await data.async_save(doc)

    hass.services.async_register(DOMAIN, SERVICE_FEED, handle_feed, schema=FEED_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_LIVESTOCK_ADD, handle_add, schema=ADD_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_LIVESTOCK_REMOVE, handle_remove, schema=REMOVE_SCHEMA
    )
