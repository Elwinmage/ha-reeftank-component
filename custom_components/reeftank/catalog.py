"""Asset catalog: fish and coral species, tank presets.

Two catalogs are merged:
- the bundled one, shipped in `custom_components/reeftank/catalog/`;
- the user one, in `<config>/reeftank/catalog/`, same layout, whose entries
  override bundled entries with the same id.

Layout (one folder per entry, named after its id):

    catalog/
      fish/<id>/species.json      + atlas pictures
      corals/<id>/species.json    + shade / mask atlases
      presets/<id>/preset.json    + view pictures

Asset file names in the descriptors are relative to their folder; the
catalog returned to the card has them turned into URLs.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)

KINDS: dict[str, str] = {
    "fish": "species.json",
    "corals": "species.json",
    "presets": "preset.json",
}

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,79}$")
_FILE_RE = re.compile(r"^[A-Za-z0-9_@.-]{1,120}$")


def _url(base_url: str, kind: str, entry_id: str, file: Any) -> Any:
    """URL of an asset named in a descriptor; anything else is left alone."""
    if isinstance(file, str) and _FILE_RE.match(file) and ".." not in file:
        return f"{base_url}/{kind}/{entry_id}/{file}"
    return file


def _resolve_assets(entry: dict[str, Any], base_url: str, kind: str) -> None:
    """Turn the asset file names of a descriptor into URLs, in place."""
    entry_id = entry["id"]
    atlas = entry.get("atlas")
    if isinstance(atlas, dict):
        entry["atlas"] = {
            k: _url(base_url, kind, entry_id, v) for k, v in atlas.items()
        }
    if isinstance(entry.get("thumbnail"), str):
        entry["thumbnail"] = _url(base_url, kind, entry_id, entry["thumbnail"])
    views = entry.get("views")
    if isinstance(views, dict):
        for view in views.values():
            if isinstance(view, dict) and isinstance(view.get("image"), str):
                view["image"] = _url(base_url, kind, entry_id, view["image"])


def scan_catalog(root: Path, base_url: str, source: str) -> dict[str, dict[str, Any]]:
    """Read one catalog directory.

    Return {kind: {id: descriptor}}; unreadable descriptors are skipped.
    """
    result: dict[str, dict[str, Any]] = {kind: {} for kind in KINDS}
    if not root.is_dir():
        return result
    for kind, descriptor in KINDS.items():
        folder = root / kind
        if not folder.is_dir():
            continue
        for entry_dir in sorted(folder.iterdir()):
            if not entry_dir.is_dir() or not _ID_RE.match(entry_dir.name):
                continue
            file = entry_dir / descriptor
            if not file.is_file():
                continue
            try:
                entry = json.loads(file.read_text(encoding="utf-8"))
            except (OSError, ValueError) as err:
                _LOGGER.warning("Catalog entry %s skipped: %s", file, err)
                continue
            if not isinstance(entry, dict):
                _LOGGER.warning("Catalog entry %s skipped: not an object", file)
                continue
            entry["id"] = entry_dir.name
            entry["source"] = source
            _resolve_assets(entry, base_url, kind)
            result[kind][entry_dir.name] = entry
    return result


def load_catalog(
    bundled_root: Path,
    bundled_url: str,
    user_root: Path,
    user_url: str,
) -> dict[str, list[dict[str, Any]]]:
    """Merge the bundled and the user catalogs (user entries win)."""
    bundled = scan_catalog(bundled_root, bundled_url, "bundled")
    user = scan_catalog(user_root, user_url, "user")
    merged: dict[str, list[dict[str, Any]]] = {}
    for kind in KINDS:
        entries = {**bundled[kind], **user[kind]}
        merged[kind] = [entries[k] for k in sorted(entries)]
    return merged
