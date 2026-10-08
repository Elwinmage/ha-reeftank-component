"""Background pictures: upload, normalisation and cleanup.

Every uploaded picture is re-encoded before it is stored:
- EXIF orientation applied, then all metadata dropped (phone pictures carry
  the GPS position of the house, and are served by a static path);
- long edge capped, so a 12 Mpx photo never reaches a wall tablet;
- WebP output.

HEIC/HEIF pictures are accepted when `pillow-heif` is installed.
"""

from __future__ import annotations

import io
import logging
import secrets
import shutil
import time
from http import HTTPStatus
from pathlib import Path
from typing import Any

from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.helpers.http import HomeAssistantView

from .const import (
    DOMAIN,
    ORPHAN_GRACE_SECONDS,
    UPLOAD_MAX_BYTES,
    UPLOAD_MAX_EDGE,
    UPLOAD_WEBP_QUALITY,
    URL_IMAGES,
    URL_UPLOAD,
)
from .models import ID_RE

_LOGGER = logging.getLogger(__name__)

ACCEPTED_FORMATS = {"JPEG", "PNG", "WEBP", "MPO", "HEIF", "HEIC"}


class ImageError(Exception):
    """A picture that cannot be accepted (the message is a translation key)."""


def _register_heif() -> bool:
    """Let Pillow open HEIC/HEIF pictures, when pillow-heif is installed."""
    try:
        from pillow_heif import register_heif_opener  # type: ignore[import-not-found]
    except ImportError:
        return False
    register_heif_opener()
    return True


def process_image(
    raw: bytes, max_edge: int = UPLOAD_MAX_EDGE
) -> tuple[bytes, int, int]:
    """Normalise an uploaded picture; return (webp bytes, width, height).

    Raises ImageError for a file that is not a supported picture.
    """
    from PIL import Image, ImageOps, UnidentifiedImageError

    _register_heif()
    try:
        image = Image.open(io.BytesIO(raw))
        image_format = (image.format or "").upper()
        if image_format not in ACCEPTED_FORMATS:
            raise ImageError("unsupported_format")
        image.load()
    except (UnidentifiedImageError, OSError, SyntaxError) as err:
        raise ImageError("unsupported_format") from err

    # Apply the orientation phones store in EXIF, then forget every tag.
    image = ImageOps.exif_transpose(image) or image
    has_alpha = image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    )
    image = image.convert("RGBA" if has_alpha else "RGB")
    image.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)

    out = io.BytesIO()
    # No exif= / icc_profile= argument: the output carries no metadata at all.
    image.save(out, format="WEBP", quality=UPLOAD_WEBP_QUALITY, method=4)
    return out.getvalue(), image.width, image.height


def write_image(root: Path, aquarium_id: str, data: bytes) -> str:
    """Store a normalised picture; return its relative path."""
    folder = root / aquarium_id
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{secrets.token_hex(8)}.webp"
    (folder / name).write_bytes(data)
    return f"{aquarium_id}/{name}"


def cleanup_orphans(
    root: Path, aquarium_id: str, keep: set[str], now: float | None = None
) -> list[str]:
    """Delete the pictures of an aquarium nothing references any more.

    Only pictures older than ORPHAN_GRACE_SECONDS go: one may have just been
    uploaded by an editor that has not saved yet. Return the deleted paths.
    """
    folder = root / aquarium_id
    if not folder.is_dir():
        return []
    now = time.time() if now is None else now
    removed: list[str] = []
    for file in folder.glob("*.webp"):
        rel = f"{aquarium_id}/{file.name}"
        if rel in keep:
            continue
        if now - file.stat().st_mtime < ORPHAN_GRACE_SECONDS:
            continue
        file.unlink(missing_ok=True)
        removed.append(rel)
    return removed


def delete_aquarium_images(root: Path, aquarium_id: str) -> None:
    """Delete every picture of an aquarium."""
    folder = root / aquarium_id
    if folder.is_dir():
        shutil.rmtree(folder, ignore_errors=True)


def image_url(path: str) -> str:
    """URL a stored picture is served at."""
    return f"{URL_IMAGES}/{path}"


class ImageUploadView(HomeAssistantView):
    """Receive a background picture for an aquarium (multipart, field `file`)."""

    url = URL_UPLOAD
    name = "api:reeftank:upload"
    requires_auth = True

    def __init__(self, data: Any) -> None:
        """Bind the view to an object giving the current `images_root`."""
        self._data = data

    async def post(self, request: web.Request, aquarium_id: str) -> web.Response:
        """Store the uploaded picture and return where it is served."""
        hass: HomeAssistant = request.app["hass"]
        user = request.get("hass_user")
        if user is None or not user.is_admin:
            return self.json_message("admin_required", HTTPStatus.UNAUTHORIZED)

        # The picture may belong to an aquarium being created: only its id
        # format is checked, the document may not exist yet.
        if not ID_RE.match(aquarium_id):
            return self.json_message("invalid_aquarium", HTTPStatus.BAD_REQUEST)

        if request.content_length and request.content_length > UPLOAD_MAX_BYTES + 4096:
            return self.json_message("too_large", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)

        try:
            reader = await request.multipart()
            field: Any = await reader.next()
            while field is not None and getattr(field, "name", None) != "file":
                field = await reader.next()
            if field is None:
                return self.json_message("no_file", HTTPStatus.BAD_REQUEST)
            chunks: list[bytes] = []
            size = 0
            while chunk := await field.read_chunk(256 * 1024):
                size += len(chunk)
                if size > UPLOAD_MAX_BYTES:
                    return self.json_message(
                        "too_large", HTTPStatus.REQUEST_ENTITY_TOO_LARGE
                    )
                chunks.append(chunk)
        except (ValueError, AssertionError) as err:
            _LOGGER.debug("Bad upload: %s", err)
            return self.json_message("no_file", HTTPStatus.BAD_REQUEST)

        raw = b"".join(chunks)
        try:
            data, width, height = await hass.async_add_executor_job(process_image, raw)
        except ImageError as err:
            return self.json_message(str(err), HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

        path = await hass.async_add_executor_job(
            write_image, self._data.images_root, aquarium_id, data
        )
        _LOGGER.debug("%s: stored %s (%sx%s)", DOMAIN, path, width, height)
        return self.json(
            {"path": path, "url": image_url(path), "width": width, "height": height}
        )
