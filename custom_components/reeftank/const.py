"""Constants of the ReefTank integration."""

from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "reeftank"

PLATFORMS: Final = [Platform.EVENT, Platform.SENSOR]

MANUFACTURER: Final = "ReefTank"
MODEL: Final = "Aquarium"

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

# Version of the stored aquarium documents (the `version` field of each one).
SCHEMA_VERSION: Final = 1

STORE_KEY: Final = DOMAIN
STORE_VERSION: Final = 1

# Everything the integration writes lives under <config>/reeftank/.
DATA_DIR: Final = "reeftank"
IMAGES_DIR: Final = "images"
USER_CATALOG_DIR: Final = "catalog"

# ---------------------------------------------------------------------------
# HTTP paths
# ---------------------------------------------------------------------------

URL_IMAGES: Final = "/reeftank/images"
URL_CATALOG_BUNDLED: Final = "/reeftank/catalog/bundled"
URL_CATALOG_USER: Final = "/reeftank/catalog/user"
URL_UPLOAD: Final = "/api/reeftank/upload/{aquarium_id}"

# ---------------------------------------------------------------------------
# Uploads
# ---------------------------------------------------------------------------

UPLOAD_MAX_BYTES: Final = 20 * 1024 * 1024
UPLOAD_MAX_EDGE: Final = 2560
UPLOAD_WEBP_QUALITY: Final = 85
# An image nobody references any more is only deleted once it is this old:
# an editor may have uploaded it a moment ago and not saved yet.
ORPHAN_GRACE_SECONDS: Final = 3600

# ---------------------------------------------------------------------------
# Render levels
# ---------------------------------------------------------------------------

RENDER_STATIC: Final = "static"
RENDER_LIGHT: Final = "light"
RENDER_FULL: Final = "full"
RENDER_LEVELS: Final = (RENDER_STATIC, RENDER_LIGHT, RENDER_FULL)

# ---------------------------------------------------------------------------
# Feeding
# ---------------------------------------------------------------------------

FEED_FEEDER: Final = "feeder"
FEED_SHORTCUT: Final = "shortcut"
FEED_MANUAL: Final = "manual"
FEED_KINDS: Final = (FEED_FEEDER, FEED_SHORTCUT, FEED_MANUAL)

DEFAULT_DEDUP_S: Final = 120
DEFAULT_FEED_DURATION_S: Final = 45

# ---------------------------------------------------------------------------
# Entities (unique id suffixes, also the translation keys)
# ---------------------------------------------------------------------------

KEY_FISH: Final = "fish"
KEY_CORALS: Final = "corals"
KEY_FEEDING: Final = "feeding"
KEY_FEEDINGS_TODAY: Final = "feedings_today"

# ---------------------------------------------------------------------------
# Dispatcher signals
# ---------------------------------------------------------------------------

# An aquarium was created: platforms add its entities.
SIGNAL_AQUARIUM_ADDED: Final = f"{DOMAIN}_aquarium_added"
# An aquarium document changed (format with the aquarium id).
SIGNAL_AQUARIUM_UPDATED: Final = f"{DOMAIN}_aquarium_updated_{{}}"
# Any aquarium changed: listing subscribers refresh.
SIGNAL_AQUARIUMS_CHANGED: Final = f"{DOMAIN}_aquariums_changed"
# A feeding was recorded (format with the aquarium id).
SIGNAL_FEEDING: Final = f"{DOMAIN}_feeding_{{}}"

# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

SERVICE_FEED: Final = "feed"
SERVICE_LIVESTOCK_ADD: Final = "livestock_add"
SERVICE_LIVESTOCK_REMOVE: Final = "livestock_remove"

ATTR_AQUARIUM: Final = "aquarium"
ATTR_SOURCE: Final = "source"
ATTR_WATER: Final = "water"
ATTR_SPECIES: Final = "species"
ATTR_COUNT: Final = "count"
ATTR_SIZE_CM: Final = "size_cm"
ATTR_NOTE: Final = "note"
ATTR_LINE_ID: Final = "line_id"
