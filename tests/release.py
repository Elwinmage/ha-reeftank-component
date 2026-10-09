"""A fake catalog release, served through aioclient_mock."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from typing import Any

BASE = "https://github.com/Elwinmage/reeftank-catalog/releases"


def entry_zip(files: dict[str, bytes | str]) -> bytes:
    """A flat zip archive."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(
                name, content.encode() if isinstance(content, str) else content
            )
    return buffer.getvalue()


def species(entry_id: str, **extra: Any) -> dict[str, bytes | str]:
    """Files of a minimal fish entry."""
    return {
        "species.json": json.dumps(
            {"kind": "fish", "atlas": {"1x": f"{entry_id}.webp"}, **extra}
        ),
        f"{entry_id}.webp": b"RIFF....WEBP",
        "thumb.webp": b"RIFF..WEBP",
    }


def release(
    version: str,
    entries: dict[str, dict[str, bytes | str]],
    **extra: Any,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Manifest and archives (by file name) of a release."""
    manifest: dict[str, Any] = {
        "format": 1,
        "version": version,
        "notes": f"Release {version}",
        "entries": {},
        **extra,
    }
    blobs: dict[str, bytes] = {}
    for key, files in entries.items():
        blob = entry_zip(files)
        name = key.replace("/", "-") + ".zip"
        blobs[name] = blob
        manifest["entries"][key] = {
            "version": version,
            "sha256": hashlib.sha256(blob).hexdigest(),
            "size": len(blob),
            "file": name,
        }
    return manifest, blobs


def publish(
    aioclient_mock: Any, manifest: dict[str, Any], blobs: dict[str, bytes]
) -> None:
    """Serve a release as the latest one."""
    aioclient_mock.clear_requests()
    aioclient_mock.get(
        f"{BASE}/latest/download/manifest.json", text=json.dumps(manifest)
    )
    for name, blob in blobs.items():
        aioclient_mock.get(
            f"{BASE}/download/{manifest['version']}/{name}", content=blob
        )
