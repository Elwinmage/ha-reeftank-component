"""Constants of the ReefTank integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "reeftank"

PLATFORMS: Final = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.EVENT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.UPDATE,
]

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
# The downloaded catalog (species of the reeftank-catalog releases).
PACK_DIR: Final = "pack"

# ---------------------------------------------------------------------------
# Catalog updates
# ---------------------------------------------------------------------------

CATALOG_REPO: Final = "Elwinmage/reeftank-catalog"
CATALOG_CHECK_HOURS: Final = 12
# Device of the catalog update entity (cannot clash with an aquarium id)
CATALOG_DEVICE_ID: Final = "__catalog__"
CONF_AUTO_UPDATE: Final = "auto_update"
DEFAULT_AUTO_UPDATE: Final = True

# ---------------------------------------------------------------------------
# HTTP paths
# ---------------------------------------------------------------------------

# Uploaded pictures are private: served by an authenticated view, reached
# from <img> through signed URLs handed out by the WebSocket API.
URL_IMAGES: Final = "/api/reeftank/images"
URL_CATALOG_PACK: Final = "/reeftank/catalog/pack"
URL_CATALOG_USER: Final = "/reeftank/catalog/user"
URL_UPLOAD: Final = "/api/reeftank/upload/{aquarium_id}"

# ---------------------------------------------------------------------------
# Uploads
# ---------------------------------------------------------------------------

# Lifetime of a signed picture URL; the card asks for fresh ones before then.
IMAGE_URL_TTL: Final = timedelta(hours=24)

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
# Monitoring
# ---------------------------------------------------------------------------

MONITORING_STORE_KEY: Final = f"{DOMAIN}.monitoring"
MONITORING_STORE_VERSION: Final = 1

CHANNEL_PH: Final = "ph"
CHANNEL_ORP: Final = "orp"
CHANNEL_CO2: Final = "co2"
CHANNELS: Final = (CHANNEL_PH, CHANNEL_ORP, CHANNEL_CO2)
# Tests rather than samples: a channel of its own for a reset only.
CHANNEL_KH: Final = "kh"
# Those have a calibration and an analysis of their own; CO2 only explains.
PROBE_CHANNELS: Final = (CHANNEL_PH, CHANNEL_ORP)

STATUS_NOT_CONFIGURED: Final = "not_configured"
STATUS_LEARNING: Final = "learning"
STATUS_PAUSED: Final = "paused"
STATUS_SETTLING: Final = "settling"
STATUS_READY: Final = "ready"
STATUSES: Final = (
    STATUS_NOT_CONFIGURED,
    STATUS_LEARNING,
    STATUS_PAUSED,
    STATUS_SETTLING,
    STATUS_READY,
)

DEFAULT_LEARNING_DAYS: Final = 14
DEFAULT_PH_BASE_DROP: Final = 0.1
DEFAULT_PH_SWING_PCT: Final = 50
DEFAULT_PH_PROFILE_BAND: Final = 0.05
DEFAULT_PH_PROFILE_HOURS: Final = 4
DEFAULT_ORP_DROP_MV: Final = 30
DEFAULT_ORP_DROP_HOURS: Final = 12
DEFAULT_PAUSE_HOURS: Final = 6
DEFAULT_KH_CHANGE_MAX: Final = 0.5

# ---------------------------------------------------------------------------
# Entities (unique id suffixes, also the translation keys)
# ---------------------------------------------------------------------------

KEY_FISH: Final = "fish"
KEY_CORALS: Final = "corals"
KEY_FEEDING: Final = "feeding"
KEY_FEEDINGS_TODAY: Final = "feedings_today"
KEY_MONITORING: Final = "monitoring"
KEY_MONITORING_PAUSE: Final = "monitoring_pause"
KEY_PH_MEAN: Final = "ph_mean_24h"
KEY_PH_SWING: Final = "ph_swing_24h"
KEY_ORP_COMPENSATED: Final = "orp_compensated"
KEY_PH_BASE_LOW: Final = "ph_base_low"
KEY_PH_SWING_HIGH: Final = "ph_swing_high"
KEY_PH_PROFILE_OFF: Final = "ph_profile_off"
KEY_ORP_LOW: Final = "orp_low"
KEY_PROBE_SUSPECT: Final = "probe_suspect"
KEY_KH_FAST_CHANGE: Final = "kh_fast_change"
KEY_KH_ESTIMATED: Final = "kh_estimated"
KEY_WATER_VOLUME: Final = "water_volume"

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
# A catalog release was installed (with its version).
SIGNAL_CATALOG_UPDATED: Final = f"{DOMAIN}_catalog_updated"
# A new analysis of an aquarium is available (format with the aquarium id).
SIGNAL_MONITORING: Final = f"{DOMAIN}_monitoring_{{}}"

# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

SERVICE_FEED: Final = "feed"
SERVICE_LIVESTOCK_ADD: Final = "livestock_add"
SERVICE_LIVESTOCK_REMOVE: Final = "livestock_remove"
SERVICE_MONITORING_CONFIGURE: Final = "monitoring_configure"
SERVICE_MONITORING_RESET: Final = "monitoring_reset"

ATTR_AQUARIUM: Final = "aquarium"
ATTR_SOURCE: Final = "source"
ATTR_WATER: Final = "water"
ATTR_SPECIES: Final = "species"
ATTR_COUNT: Final = "count"
ATTR_SIZE_CM: Final = "size_cm"
ATTR_NOTE: Final = "note"
ATTR_LINE_ID: Final = "line_id"
ATTR_CHANNEL: Final = "channel"
