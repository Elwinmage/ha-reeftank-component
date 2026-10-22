"""Background pictures: upload, normalisation and cleanup.

Every uploaded picture is re-encoded before it is stored:
- EXIF orientation applied, then all metadata dropped (phone pictures carry
  the GPS position of the house);
- long edge capped, so a 12 Mpx photo never reaches a wall tablet;
- WebP output.

HEIC/HEIF pictures are accepted when `pillow-heif` is installed.

The pictures show the user's home: they are only served to authenticated
requests (`ImageView`). An `<img>` cannot send the bearer token, so the
WebSocket API and the upload view hand out URLs signed for the user's
refresh token (`signed_image_url`), valid IMAGE_URL_TTL.
"""

from __future__ import annotations

import io
import logging
import secrets
import shutil
import time
from collections.abc import Iterable
from http import HTTPStatus
from pathlib import Path
from typing import Any

from aiohttp import hdrs, web
from homeassistant.components.http.auth import async_sign_path
from homeassistant.components.http.const import KEY_HASS_REFRESH_TOKEN_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.http import HomeAssistantView

from .const import (
    DOMAIN,
    IMAGE_URL_TTL,
    ORPHAN_GRACE_SECONDS,
    UPLOAD_MAX_BYTES,
    UPLOAD_MAX_EDGE,
    UPLOAD_WEBP_QUALITY,
    URL_IMAGES,
    URL_UPLOAD,
)
from .models import ID_RE, UPLOAD_RE

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
    """URL a stored picture is served at (needs authentication)."""
    return f"{URL_IMAGES}/{path}"


@callback
def signed_image_url(
    hass: HomeAssistant, path: str, refresh_token_id: str | None
) -> str:
    """URL of a stored picture usable without auth header, for one user.

    The signature is bound to the refresh token: it stops working when the
    user logs out or the token is revoked, and after IMAGE_URL_TTL.
    """
    return async_sign_path(
        hass, image_url(path), IMAGE_URL_TTL, refresh_token_id=refresh_token_id
    )


@callback
def signed_image_urls(
    hass: HomeAssistant, paths: Iterable[str], refresh_token_id: str | None
) -> dict[str, str]:
    """Signed URLs of the valid uploaded pictures among `paths`."""
    return {
        path: signed_image_url(hass, path, refresh_token_id)
        for path in sorted(set(paths))
        if isinstance(path, str) and UPLOAD_RE.match(path)
    }


def _image_file(root: Path, aquarium_id: str, name: str) -> Path | None:
    """The stored picture for a request, or None (never outside `root`)."""
    if not UPLOAD_RE.match(f"{aquarium_id}/{name}"):
        return None
    file = root / aquarium_id / name
    return file if file.is_file() else None


class ImageView(HomeAssistantView):
    """Serve the uploaded pictures to authenticated requests only.

    Authentication is a bearer token or a signed URL (`authSig`), checked by
    the Home Assistant auth middleware before `get` runs.
    """

    url = URL_IMAGES + "/{aquarium_id}/{name}"
    name = "api:reeftank:image"
    requires_auth = True

    def __init__(self, data: Any) -> None:
        """Bind the view to an object giving the current `images_root`."""
        self._data = data

    async def get(
        self, request: web.Request, aquarium_id: str, name: str
    ) -> web.StreamResponse:
        """Return the picture, or 404 for anything else."""
        hass: HomeAssistant = request.app["hass"]
        file = await hass.async_add_executor_job(
            _image_file, self._data.images_root, aquarium_id, name
        )
        if file is None:
            return web.Response(status=HTTPStatus.NOT_FOUND)
        return web.FileResponse(
            file,
            headers={
                hdrs.CONTENT_TYPE: "image/webp",
                # Names are random and never rewritten, but the content is
                # private: browser cache only, never a shared proxy cache.
                hdrs.CACHE_CONTROL: "private, max-age=86400, immutable",
                "X-Content-Type-Options": "nosniff",
            },
        )


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
        url = signed_image_url(hass, path, request.get(KEY_HASS_REFRESH_TOKEN_ID))
        return self.json({"path": path, "url": url, "width": width, "height": height})
