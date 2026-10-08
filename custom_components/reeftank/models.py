"""Aquarium documents: validation, defaults and livestock helpers.

An aquarium document is everything the card needs to draw one tank: its
waters (main tank, sump...), its views (pictures), its livestock and the
sources of its feeding events. See README.md, "Data model".

This module is pure: no Home Assistant object, so it is easy to test and
the same rules apply whether a document comes from the card, a service call
or the store.
"""

from __future__ import annotations

import math
import re
import secrets
from collections import Counter
from collections.abc import Callable
from copy import deepcopy
from typing import Any, cast

import voluptuous as vol

from .const import (
    DEFAULT_DEDUP_S,
    DEFAULT_FEED_DURATION_S,
    FEED_KINDS,
    RENDER_FULL,
    RENDER_LEVELS,
    SCHEMA_VERSION,
    URL_CATALOG_BUNDLED,
    URL_CATALOG_USER,
)

# Ids are short, url-safe and generated server side when missing.
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}$")
# An uploaded picture: "<aquarium id>/<file>.webp", relative to the images dir.
_UPLOAD_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}/[A-Za-z0-9_-]{1,64}\.webp$")
# A catalog picture (preset): served by the integration itself.
_CATALOG_RE = re.compile(
    r"^(?:"
    + re.escape(URL_CATALOG_BUNDLED)
    + "|"
    + re.escape(URL_CATALOG_USER)
    + r")/[A-Za-z0-9_./-]{1,200}$"
)
_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

ROLE_FEEDING_POINT = "feeding_point"
ELEMENT_KINDS = ("device", "entity", "marker")
LIVESTOCK_KINDS = ("fish", "invertebrate")
PHOTO_LIGHTS = ("white", "blue")

MAX_NAME = 100
MAX_NOTE = 500
MAX_POLY_POINTS = 400


def new_id(length: int = 8) -> str:
    """Return a new short id (lowercase hex)."""
    return secrets.token_hex(length // 2)


# ---------------------------------------------------------------------------
# Elementary validators
# ---------------------------------------------------------------------------


def _ident(value: Any) -> str:
    """An id: short, lowercase, url-safe."""
    if not isinstance(value, str) or not ID_RE.match(value):
        raise vol.Invalid(f"invalid id: {value!r}")
    return value


def _unit(value: Any) -> float:
    """A coordinate or a depth, clamped into 0..1."""
    try:
        number = float(value)
    except (TypeError, ValueError) as err:
        raise vol.Invalid(f"not a number: {value!r}") from err
    if math.isnan(number):
        raise vol.Invalid("not a number: NaN")
    return min(1.0, max(0.0, number))


def _point(value: Any) -> list[float]:
    """A point of a picture, as [x, y] normalised to 0..1."""
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise vol.Invalid(f"invalid point: {value!r}")
    return [_unit(value[0]), _unit(value[1])]


def _quad(value: Any) -> list[list[float]]:
    """A water outline: 4 corners, or none at all (not outlined yet)."""
    if not isinstance(value, list) or len(value) not in (0, 4):
        raise vol.Invalid("a quad has 4 corners (or none)")
    return [_point(p) for p in value]


def _polygon(value: Any) -> list[list[float]]:
    """A decor or hotspot outline: 3 points at least."""
    if not isinstance(value, list) or not 3 <= len(value) <= MAX_POLY_POINTS:
        raise vol.Invalid(f"a polygon has 3 to {MAX_POLY_POINTS} points")
    return [_point(p) for p in value]


def _hex_color(value: Any) -> str:
    if not isinstance(value, str) or not _HEX_RE.match(value):
        raise vol.Invalid(f"invalid colour: {value!r}")
    return value.lower()


def _date(value: Any) -> str:
    if not isinstance(value, str) or not _DATE_RE.match(value):
        raise vol.Invalid(f"invalid date: {value!r}")
    return value


def _image(value: Any) -> str | None:
    """A view picture: an uploaded file or a catalog picture."""
    if value in (None, ""):
        return None
    if isinstance(value, str) and (_UPLOAD_RE.match(value) or _CATALOG_RE.match(value)):
        if ".." in value:
            raise vol.Invalid("invalid image path")
        return value
    raise vol.Invalid(f"invalid image: {value!r}")


def _size_range(value: Any) -> list[float]:
    """A size range in cm: [min, max], min <= max."""
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise vol.Invalid("a size range is [min, max]")
    low, high = (
        vol.All(vol.Coerce(float), vol.Range(min=0.1, max=500))(v) for v in value
    )
    return [min(low, high), max(low, high)]


def _entity_id(value: Any) -> str:
    if not isinstance(value, str) or not re.match(r"^[a-z_]+\.[a-z0-9_]+$", value):
        raise vol.Invalid(f"invalid entity id: {value!r}")
    return value


def _text(max_len: int) -> Callable[[Any], str]:
    return vol.All(str, vol.Length(max=max_len))


def _with_id(schema: dict[Any, Any]) -> vol.All:
    """A list item carrying an id, generated when missing."""

    def ensure(item: Any) -> Any:
        if isinstance(item, dict) and not item.get("id"):
            item = {**item, "id": new_id()}
        return item

    return vol.All(ensure, vol.Schema({vol.Required("id"): _ident, **schema}))


# ---------------------------------------------------------------------------
# Document schema
# ---------------------------------------------------------------------------

LIGHT_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Optional("device_id"): vol.All(str, vol.Length(min=1, max=64)),
            vol.Optional("entity_id"): _entity_id,
            vol.Optional("x", default=0.5): _unit,
        }
    ),
    vol.Any(
        vol.Schema({vol.Required("device_id"): str}, extra=vol.ALLOW_EXTRA),
        vol.Schema({vol.Required("entity_id"): str}, extra=vol.ALLOW_EXTRA),
        msg="a light names a device_id or an entity_id",
    ),
)

LIVESTOCK_SCHEMA = _with_id(
    {
        vol.Optional("kind", default="fish"): vol.In(LIVESTOCK_KINDS),
        vol.Required("species"): vol.All(str, vol.Length(min=1, max=MAX_NAME)),
        vol.Optional("name", default=""): _text(MAX_NAME),
        vol.Optional("count", default=1): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=10000)
        ),
        vol.Optional("size_cm"): vol.Any(None, _size_range),
        vol.Optional("added"): vol.Any(None, _date),
        vol.Optional("note", default=""): _text(MAX_NOTE),
    }
)

CORAL_SCHEMA = _with_id(
    {
        vol.Required("species"): vol.All(str, vol.Length(min=1, max=MAX_NAME)),
        vol.Optional("name", default=""): _text(MAX_NAME),
        vol.Optional("view"): vol.Any(None, _ident),
        vol.Optional("pos", default=[0.5, 0.8]): _point,
        vol.Optional("z", default=0.5): _unit,
        vol.Optional("size_cm", default=10.0): vol.All(
            vol.Coerce(float), vol.Range(min=0.5, max=200)
        ),
        vol.Optional("palette", default=list): vol.All([_hex_color], vol.Length(max=4)),
        vol.Optional("added"): vol.Any(None, _date),
        vol.Optional("note", default=""): _text(MAX_NOTE),
    }
)

WATER_SCHEMA = vol.Schema(
    {
        vol.Optional("name", default=""): _text(MAX_NAME),
        vol.Optional("lights", default=list): [LIGHT_SCHEMA],
        vol.Optional("flow", default=list): [_entity_id],
        vol.Optional("sand_band", default=0.12): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=0.5)
        ),
        vol.Optional("livestock", default=list): [LIVESTOCK_SCHEMA],
        vol.Optional("corals", default=list): [CORAL_SCHEMA],
    }
)

REGION_SCHEMA = vol.Schema(
    {
        vol.Required("water"): _ident,
        vol.Optional("quad", default=list): _quad,
    }
)

DECOR_SCHEMA = _with_id(
    {
        vol.Optional("z", default=0.5): _unit,
        vol.Required("poly"): _polygon,
    }
)

ELEMENT_SCHEMA = _with_id(
    {
        vol.Required("kind"): vol.In(ELEMENT_KINDS),
        vol.Optional("device_id"): vol.All(str, vol.Length(min=1, max=64)),
        vol.Optional("entity_id"): _entity_id,
        # Card element rendering an entity (common-sensor, common-switch...)
        vol.Optional("type"): vol.All(str, vol.Match(r"^[a-z][a-z0-9-]{1,40}$")),
        vol.Required("pos"): _point,
        vol.Optional("scale", default=1.0): vol.All(
            vol.Coerce(float), vol.Range(min=0.2, max=5)
        ),
        vol.Optional("label", default=""): _text(MAX_NAME),
        vol.Optional("roles", default=list): [vol.In([ROLE_FEEDING_POINT])],
        vol.Optional("source"): vol.Any(None, _ident),
    }
)

HOTSPOT_SCHEMA = _with_id(
    {
        vol.Required("poly"): _polygon,
        vol.Required("goto"): _ident,
        vol.Optional("label", default=""): _text(MAX_NAME),
    }
)

VIEW_SCHEMA = vol.Schema(
    {
        vol.Optional("name", default=""): _text(MAX_NAME),
        vol.Optional("image"): _image,
        vol.Optional("regions", default=list): [REGION_SCHEMA],
        vol.Optional("decor", default=list): [DECOR_SCHEMA],
        vol.Optional("elements", default=list): [ELEMENT_SCHEMA],
        vol.Optional("hotspots", default=list): [HOTSPOT_SCHEMA],
    }
)

FEED_SOURCE_SCHEMA = _with_id(
    {
        vol.Optional("type", default="entity"): vol.In(["entity"]),
        vol.Required("entity_id"): _entity_id,
        vol.Optional("kind"): vol.Any(None, vol.In(FEED_KINDS)),
    }
)

FEEDING_SCHEMA = vol.Schema(
    {
        vol.Optional("sources", default=list): [FEED_SOURCE_SCHEMA],
        vol.Optional("dedup_s", default=DEFAULT_DEDUP_S): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=3600)
        ),
        vol.Optional("duration_s", default=DEFAULT_FEED_DURATION_S): vol.All(
            vol.Coerce(int), vol.Range(min=5, max=600)
        ),
    }
)

DIMENSIONS_SCHEMA = vol.Schema(
    {
        # Red Sea cloud naming: length = X (front), width = Y (depth)
        vol.Required("length"): vol.All(vol.Coerce(float), vol.Range(min=1, max=2000)),
        vol.Required("width"): vol.All(vol.Coerce(float), vol.Range(min=1, max=2000)),
        vol.Required("height"): vol.All(vol.Coerce(float), vol.Range(min=1, max=2000)),
    }
)

RENDER_SCHEMA = vol.Schema(
    {
        vol.Optional("level", default=RENDER_FULL): vol.In(RENDER_LEVELS),
        vol.Optional("max_fish", default=30): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=200)
        ),
        vol.Optional("caustics", default=False): bool,
    }
)

DOCUMENT_SCHEMA = vol.Schema(
    {
        vol.Optional("version", default=SCHEMA_VERSION): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=SCHEMA_VERSION)
        ),
        vol.Optional("id"): _ident,
        vol.Optional("revision", default=0): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Required("name"): vol.All(str, vol.Strip, vol.Length(min=1, max=MAX_NAME)),
        vol.Optional("cloud"): vol.Any(
            None,
            vol.Schema(
                {
                    vol.Required("provider"): vol.All(str, vol.Length(min=1, max=40)),
                    vol.Required("uid"): vol.All(str, vol.Length(min=1, max=100)),
                }
            ),
        ),
        vol.Optional("preset"): vol.Any(None, vol.All(str, vol.Length(max=200))),
        vol.Optional("dimensions_cm"): vol.Any(None, DIMENSIONS_SCHEMA),
        vol.Optional("photo_light", default="white"): vol.In(PHOTO_LIGHTS),
        vol.Optional("render", default=dict): RENDER_SCHEMA,
        vol.Optional("waters", default=dict): {_ident: WATER_SCHEMA},
        vol.Optional("feeding", default=dict): FEEDING_SCHEMA,
        vol.Optional("views", default=dict): {_ident: VIEW_SCHEMA},
        vol.Optional("default_view"): vol.Any(None, _ident),
    }
)


def _check_links(doc: dict[str, Any]) -> None:
    """Check the references between the parts of a document."""
    waters = doc["waters"]
    views = doc["views"]
    source_ids = {s["id"] for s in doc["feeding"]["sources"]}

    if doc.get("default_view") and doc["default_view"] not in views:
        raise vol.Invalid(f"default_view {doc['default_view']!r} is not a view")

    for view_id, view in views.items():
        for region in view["regions"]:
            if region["water"] not in waters:
                raise vol.Invalid(
                    f"view {view_id!r}: region of unknown water {region['water']!r}"
                )
        for hotspot in view["hotspots"]:
            if hotspot["goto"] not in views:
                raise vol.Invalid(
                    f"view {view_id!r}: hotspot to unknown view {hotspot['goto']!r}"
                )
        for element in view["elements"]:
            kind = element["kind"]
            if kind == "device" and not element.get("device_id"):
                raise vol.Invalid(f"view {view_id!r}: device element without device_id")
            if kind == "entity" and not element.get("entity_id"):
                raise vol.Invalid(f"view {view_id!r}: entity element without entity_id")
            source = element.get("source")
            if source and source not in source_ids:
                raise vol.Invalid(
                    f"view {view_id!r}: element bound to unknown feeding source {source!r}"
                )

    for water_id, water in waters.items():
        for coral in water["corals"]:
            if coral.get("view") and coral["view"] not in views:
                raise vol.Invalid(
                    f"water {water_id!r}: coral on unknown view {coral['view']!r}"
                )


def _check_unique_ids(doc: dict[str, Any]) -> None:
    """Ids of list items must be unique in their document."""
    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    for water in doc["waters"].values():
        items += water["livestock"] + water["corals"]
    for view in doc["views"].values():
        items += view["decor"] + view["elements"] + view["hotspots"]
    items += doc["feeding"]["sources"]
    for item in items:
        if item["id"] in seen:
            raise vol.Invalid(f"duplicate id {item['id']!r}")
        seen.add(item["id"])


def validate_document(data: Any) -> dict[str, Any]:
    """Validate a document and fill its defaults.

    Raises vol.Invalid when the document is malformed. The input is not
    modified.
    """
    doc = cast(dict[str, Any], DOCUMENT_SCHEMA(deepcopy(data)))
    _check_unique_ids(doc)
    _check_links(doc)
    if not doc.get("default_view") and doc["views"]:
        doc["default_view"] = next(iter(doc["views"]))
    return doc


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


def livestock_counts(doc: dict[str, Any]) -> dict[str, int]:
    """Number of animals per species (fish and invertebrates), all waters."""
    counts: Counter[str] = Counter()
    for water in doc.get("waters", {}).values():
        for line in water.get("livestock", []):
            counts[line.get("name") or line["species"]] += int(line.get("count", 0))
    return {k: v for k, v in sorted(counts.items()) if v > 0}


def fish_counts(doc: dict[str, Any]) -> dict[str, int]:
    """Number of fish per species, all waters."""
    counts: Counter[str] = Counter()
    for water in doc.get("waters", {}).values():
        for line in water.get("livestock", []):
            if line.get("kind", "fish") == "fish":
                counts[line.get("name") or line["species"]] += int(line.get("count", 0))
    return {k: v for k, v in sorted(counts.items()) if v > 0}


def coral_counts(doc: dict[str, Any]) -> dict[str, int]:
    """Number of coral colonies per species, all waters."""
    counts: Counter[str] = Counter()
    for water in doc.get("waters", {}).values():
        for coral in water.get("corals", []):
            counts[coral.get("name") or coral["species"]] += 1
    return dict(sorted(counts.items()))


def livestock_add(
    doc: dict[str, Any],
    water_id: str,
    species: str,
    count: int,
    *,
    kind: str = "fish",
    size_cm: list[float] | None = None,
    note: str | None = None,
    added: str | None = None,
) -> dict[str, Any]:
    """Add animals to a water, merging with the line of the same species.

    Returns the inventory line that was created or updated. The water is
    created when missing.
    """
    if count < 1:
        raise vol.Invalid("count must be at least 1")
    water = doc.setdefault("waters", {}).setdefault(water_id, WATER_SCHEMA({}))
    for line in water["livestock"]:
        if line["species"] == species and line.get("kind", "fish") == kind:
            line["count"] = int(line.get("count", 0)) + count
            if size_cm:
                line["size_cm"] = _size_range(size_cm)
            if note:
                line["note"] = note
            return line
    line = cast(
        dict[str, Any],
        LIVESTOCK_SCHEMA(
            {
                "kind": kind,
                "species": species,
                "count": count,
                "size_cm": size_cm,
                "note": note or "",
                "added": added,
            }
        ),
    )
    water["livestock"].append(line)
    return line


def livestock_remove(
    doc: dict[str, Any],
    count: int,
    *,
    line_id: str | None = None,
    species: str | None = None,
) -> dict[str, Any] | None:
    """Remove animals from an inventory line, dropping it when empty.

    The line is named by its id, or by its species (first line found).
    Returns the updated line, or None when it was dropped. Raises KeyError
    when no line matches.
    """
    if count < 1:
        raise vol.Invalid("count must be at least 1")
    for water in doc.get("waters", {}).values():
        for line in water["livestock"]:
            if (line_id and line["id"] == line_id) or (
                not line_id and species and line["species"] == species
            ):
                line["count"] = max(0, int(line.get("count", 0)) - count)
                if line["count"] == 0:
                    water["livestock"].remove(line)
                    return None
                return line
    raise KeyError(line_id or species or "")


def referenced_images(doc: dict[str, Any]) -> set[str]:
    """Uploaded pictures a document uses (relative paths)."""
    return {
        view["image"]
        for view in doc.get("views", {}).values()
        if view.get("image") and _UPLOAD_RE.match(view["image"])
    }


def feeding_points(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Elements of every view acting as a feeding point."""
    return [
        element
        for view in doc.get("views", {}).values()
        for element in view.get("elements", [])
        if ROLE_FEEDING_POINT in element.get("roles", [])
    ]
