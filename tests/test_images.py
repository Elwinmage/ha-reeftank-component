"""Picture normalisation, storage and the upload view."""

from __future__ import annotations

import io
import os
import sys
import time
import types
from http import HTTPStatus
from pathlib import Path
from typing import Any
from unittest.mock import patch

import aiohttp
import pytest
from homeassistant.core import HomeAssistant
from PIL import Image
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.reeftank import images
from custom_components.reeftank.const import ORPHAN_GRACE_SECONDS
from custom_components.reeftank.images import (
    ImageError,
    cleanup_orphans,
    delete_aquarium_images,
    image_url,
    process_image,
    write_image,
)


def _jpeg_with_exif(width: int = 400, height: int = 200, orientation: int = 6) -> bytes:
    """A JPEG stored sideways, with an orientation tag and a GPS block."""
    image = Image.new("RGB", (width, height), (200, 30, 30))
    exif = Image.Exif()
    exif[0x0112] = orientation  # Orientation
    exif[0x8825] = {1: "N", 2: (44.0, 50.0, 0.0)}  # GPSInfo
    out = io.BytesIO()
    image.save(out, format="JPEG", exif=exif)
    return out.getvalue()


def _png(mode: str = "RGBA", size: tuple[int, int] = (64, 32)) -> bytes:
    image = Image.new(mode, size)
    if mode == "P":
        image.info["transparency"] = 0
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def test_jpeg_is_rotated_and_stripped() -> None:
    data, width, height = process_image(_jpeg_with_exif())
    # Orientation 6: stored landscape, displayed portrait
    assert (width, height) == (200, 400)
    out = Image.open(io.BytesIO(data))
    assert out.format == "WEBP"
    assert out.mode == "RGB"
    assert not out.getexif()
    assert "exif" not in out.info


def test_alpha_is_kept() -> None:
    data, _, _ = process_image(_png("RGBA"))
    assert Image.open(io.BytesIO(data)).mode == "RGBA"
    data, _, _ = process_image(_png("P"))
    assert Image.open(io.BytesIO(data)).mode == "RGBA"
    data, _, _ = process_image(_png("L"))
    assert Image.open(io.BytesIO(data)).mode == "RGB"


def test_long_edge_is_capped() -> None:
    _, width, height = process_image(_png("RGB", (3000, 1500)), max_edge=1000)
    assert (width, height) == (1000, 500)


def test_unsupported_files() -> None:
    gif = io.BytesIO()
    Image.new("RGB", (4, 4)).save(gif, format="GIF")
    with pytest.raises(ImageError, match="unsupported_format"):
        process_image(gif.getvalue())
    with pytest.raises(ImageError, match="unsupported_format"):
        process_image(b"not a picture")


def test_heif_opener_is_registered_when_available() -> None:
    calls: list[bool] = []
    module = types.ModuleType("pillow_heif")
    module.register_heif_opener = lambda: calls.append(True)  # type: ignore[attr-defined]
    with patch.dict(sys.modules, {"pillow_heif": module}):
        assert images._register_heif() is True
    assert calls == [True]
    with patch.dict(sys.modules, {"pillow_heif": None}):
        assert images._register_heif() is False


def test_write_cleanup_delete(tmp_path: Path) -> None:
    kept = write_image(tmp_path, "a1b2", b"kept")
    old = write_image(tmp_path, "a1b2", b"old")
    fresh = write_image(tmp_path, "a1b2", b"fresh")
    assert kept.startswith("a1b2/") and kept.endswith(".webp")
    past = time.time() - ORPHAN_GRACE_SECONDS - 10
    for rel in (kept, old):
        os.utime(tmp_path / rel, (past, past))

    removed = cleanup_orphans(tmp_path, "a1b2", {kept})
    assert removed == [old]
    assert (tmp_path / kept).exists()
    assert (tmp_path / fresh).exists(), "recent uploads are kept"
    assert cleanup_orphans(tmp_path, "ghost", set()) == []

    delete_aquarium_images(tmp_path, "a1b2")
    assert not (tmp_path / "a1b2").exists()
    delete_aquarium_images(tmp_path, "a1b2")  # no folder: nothing to do
    assert image_url(kept) == f"/reeftank/images/{kept}"


async def _upload(client: Any, url: str, payload: bytes, name: str = "file") -> Any:
    form = aiohttp.FormData()
    form.add_field(name, payload, filename="photo.jpg", content_type="image/jpeg")
    return await client.post(url, data=form)


async def test_upload_view(
    hass: HomeAssistant, entry: MockConfigEntry, hass_client: Any
) -> None:
    client = await hass_client()
    response = await _upload(client, "/api/reeftank/upload/a1b2", _jpeg_with_exif())
    assert response.status == HTTPStatus.OK
    body = await response.json()
    assert body["width"] == 200 and body["height"] == 400
    assert body["url"] == f"/reeftank/images/{body['path']}"
    stored = entry.runtime_data.images_root / body["path"]
    assert stored.is_file()

    # The picture is served by the static path
    served = await client.get(body["url"])
    assert served.status == HTTPStatus.OK


async def test_upload_errors(
    hass: HomeAssistant, entry: MockConfigEntry, hass_client: Any
) -> None:
    client = await hass_client()

    response = await _upload(client, "/api/reeftank/upload/BAD!", _png())
    assert response.status == HTTPStatus.BAD_REQUEST

    response = await _upload(client, "/api/reeftank/upload/a1b2", _png(), name="other")
    assert response.status == HTTPStatus.BAD_REQUEST

    response = await _upload(client, "/api/reeftank/upload/a1b2", b"garbage")
    assert response.status == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    assert (await response.json())["message"] == "unsupported_format"

    response = await client.post(
        "/api/reeftank/upload/a1b2",
        data=b"x",
        headers={"Content-Type": "text/plain"},
    )
    assert response.status == HTTPStatus.BAD_REQUEST

    with patch.object(images, "UPLOAD_MAX_BYTES", 10):
        response = await _upload(client, "/api/reeftank/upload/a1b2", _png())
        assert response.status == HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    with patch.object(images, "UPLOAD_MAX_BYTES", -5000):
        response = await _upload(client, "/api/reeftank/upload/a1b2", _png())
        assert response.status == HTTPStatus.REQUEST_ENTITY_TOO_LARGE


async def test_upload_needs_admin(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    hass_client: Any,
    hass_read_only_access_token: str,
) -> None:
    client = await hass_client(hass_read_only_access_token)
    response = await _upload(client, "/api/reeftank/upload/a1b2", _png())
    assert response.status == HTTPStatus.UNAUTHORIZED
