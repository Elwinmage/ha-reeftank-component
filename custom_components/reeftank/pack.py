"""Downloaded catalog ("pack"): the species published by reeftank-catalog.

Every release of the catalog repository holds a `manifest.json` and one zip
archive per entry (a species folder, flat):

    {
      "format": 1,
      "version": "2026.10.0",
      "min_integration": "0.1.0",
      "notes": "Added: siganus_vulpinus",
      "entries": {
        "fish/siganus_vulpinus": {
          "version": "2026.10.0",
          "sha256": "<hex>",
          "size": 830000,
          "file": "fish-siganus_vulpinus.zip"
        }
      }
    }

The pack is installed in `<config>/reeftank/pack/` (same layout as a
catalog, plus the manifest of the installed release). An update only
downloads the entries that changed: the others are copied from the current
pack into a staging folder, which then replaces the pack in one move, so
that an interrupted update leaves the previous pack untouched.

Archives are checked before use: sha256 and size from the manifest, flat
file names, picture and JSON files only, bounded sizes, and a descriptor
that parses.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

import aiohttp
from awesomeversion import AwesomeVersion, AwesomeVersionException

MANIFEST_FILE = "manifest.json"
MANIFEST_FORMAT = 1
#: Kinds a pack may hold, with the descriptor every entry must have
PACK_KINDS: dict[str, str] = {
    "fish": "species.json",
    "corals": "species.json",
    "textures": "texture.json",
}
ALLOWED_SUFFIXES = (".json", ".webp", ".png")
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_ENTRY_BYTES = 32 * 1024 * 1024
MAX_ENTRY_FILES = 16
DOWNLOAD_TIMEOUT_S = 120

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,79}$")
_FILE_RE = re.compile(r"^[A-Za-z0-9_@.-]{1,120}$")
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_VERSION_RE = re.compile(r"^[0-9A-Za-z._+-]{1,40}$")


class PackError(Exception):
    """A manifest or an archive that cannot be used."""


@dataclass(frozen=True)
class PackEntry:
    """One entry of a manifest."""

    key: str
    version: str
    sha256: str
    size: int
    file: str

    @property
    def kind(self) -> str:
        """`fish`, `corals` or `textures`."""
        return self.key.split("/", 1)[0]

    @property
    def entry_id(self) -> str:
        """The entry id (its folder name)."""
        return self.key.split("/", 1)[1]


@dataclass
class Manifest:
    """A parsed manifest."""

    version: str
    min_integration: str | None = None
    notes: str = ""
    entries: dict[str, PackEntry] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


def parse_manifest(data: Any) -> Manifest:
    """Check and parse a manifest. Raises PackError."""
    if not isinstance(data, dict):
        raise PackError("manifest is not an object")
    if data.get("format") != MANIFEST_FORMAT:
        raise PackError(f"unsupported manifest format {data.get('format')!r}")
    version = data.get("version")
    if not isinstance(version, str) or not _VERSION_RE.match(version):
        raise PackError(f"bad manifest version {version!r}")
    minimum = data.get("min_integration")
    if minimum is not None and (
        not isinstance(minimum, str) or not _VERSION_RE.match(minimum)
    ):
        raise PackError(f"bad min_integration {minimum!r}")
    notes = data.get("notes", "")
    if not isinstance(notes, str):
        raise PackError("notes must be a text")
    raw_entries = data.get("entries")
    if not isinstance(raw_entries, dict):
        raise PackError("entries must be an object")
    entries: dict[str, PackEntry] = {}
    for key, item in raw_entries.items():
        kind, _, entry_id = str(key).partition("/")
        if kind not in PACK_KINDS or not _ID_RE.match(entry_id):
            raise PackError(f"bad entry key {key!r}")
        if not isinstance(item, dict):
            raise PackError(f"entry {key} is not an object")
        sha = item.get("sha256")
        size = item.get("size")
        file = item.get("file")
        entry_version = item.get("version", version)
        if not isinstance(sha, str) or not _SHA_RE.match(sha):
            raise PackError(f"entry {key}: bad sha256")
        if not isinstance(size, int) or not 0 < size <= MAX_ENTRY_BYTES:
            raise PackError(f"entry {key}: bad size")
        if not isinstance(file, str) or not _FILE_RE.match(file):
            raise PackError(f"entry {key}: bad file name")
        if not isinstance(entry_version, str) or not _VERSION_RE.match(entry_version):
            raise PackError(f"entry {key}: bad version")
        entries[key] = PackEntry(key, entry_version, sha, size, file)
    return Manifest(version, minimum, notes, entries, data)


def is_compatible(manifest: Manifest, integration_version: str) -> bool:
    """True when this integration can use the manifest's entries."""
    if not manifest.min_integration:
        return True
    try:
        return AwesomeVersion(integration_version.lstrip("v")) >= AwesomeVersion(
            manifest.min_integration.lstrip("v")
        )
    except AwesomeVersionException:  # pragma: no cover - checked by the regex
        return False


def read_installed(root: Path) -> Manifest | None:
    """Manifest of the installed pack, or None.

    None too when an entry it lists is missing on disk (a restored backup
    without the pack, a folder deleted by hand): the pack is then installed
    again.
    """
    file = root / MANIFEST_FILE
    try:
        manifest = parse_manifest(json.loads(file.read_text(encoding="utf-8")))
    except (OSError, ValueError, PackError):
        return None
    for entry in manifest.entries.values():
        descriptor = root / entry.kind / entry.entry_id / PACK_KINDS[entry.kind]
        if not descriptor.is_file():
            return None
    return manifest


def plan(
    installed: Manifest | None, latest: Manifest
) -> tuple[list[PackEntry], list[PackEntry]]:
    """Entries to keep from the installed pack, and entries to download."""
    keep: list[PackEntry] = []
    fetch: list[PackEntry] = []
    current = installed.entries if installed else {}
    for key, entry in sorted(latest.entries.items()):
        old = current.get(key)
        if old is not None and old.sha256 == entry.sha256:
            keep.append(entry)
        else:
            fetch.append(entry)
    return keep, fetch


def verify(blob: bytes, entry: PackEntry) -> None:
    """Check a downloaded archive against its manifest entry."""
    if len(blob) != entry.size:
        raise PackError(f"{entry.key}: {len(blob)} bytes, expected {entry.size}")
    if hashlib.sha256(blob).hexdigest() != entry.sha256:
        raise PackError(f"{entry.key}: checksum mismatch")


def extract_entry(blob: bytes, kind: str, dest: Path) -> None:
    """Extract an entry archive into `dest` (flat), after checking it."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(blob))
    except zipfile.BadZipFile as err:
        raise PackError(f"{dest.name}: not a zip archive") from err
    with archive:
        infos = [i for i in archive.infolist() if not i.is_dir()]
        if not infos or len(infos) > MAX_ENTRY_FILES:
            raise PackError(f"{dest.name}: {len(infos)} files")
        total = 0
        for info in infos:
            name = PurePosixPath(info.filename).name
            if (
                info.filename != name
                or not _FILE_RE.match(name)
                or not name.lower().endswith(ALLOWED_SUFFIXES)
            ):
                raise PackError(f"{dest.name}: unexpected file {info.filename!r}")
            total += info.file_size
        if total > MAX_ENTRY_BYTES:
            raise PackError(f"{dest.name}: too big once extracted")
        descriptor = PACK_KINDS[kind]
        if descriptor not in {i.filename for i in infos}:
            raise PackError(f"{dest.name}: no {descriptor}")
        try:
            parsed = json.loads(archive.read(descriptor).decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as err:
            raise PackError(f"{dest.name}: unreadable {descriptor}") from err
        if not isinstance(parsed, dict):
            raise PackError(f"{dest.name}: {descriptor} is not an object")
        dest.mkdir(parents=True, exist_ok=True)
        for info in infos:
            (dest / info.filename).write_bytes(archive.read(info))


def staging_dir(root: Path) -> Path:
    """Folder an update is prepared in, next to the pack."""
    return root.with_name(root.name + ".new")


def prepare_staging(root: Path, keep: list[PackEntry]) -> Path:
    """A fresh staging folder holding the kept entries of the pack."""
    staging = staging_dir(root)
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    for entry in keep:
        source = root / entry.kind / entry.entry_id
        shutil.copytree(source, staging / entry.kind / entry.entry_id)
    return staging


def commit(root: Path, staging: Path, manifest: Manifest) -> None:
    """Write the manifest, then put the staging folder in place of the pack."""
    (staging / MANIFEST_FILE).write_text(
        json.dumps(manifest.raw, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    old = root.with_name(root.name + ".old")
    shutil.rmtree(old, ignore_errors=True)
    if root.exists():
        root.rename(old)
    staging.rename(root)
    shutil.rmtree(old, ignore_errors=True)


async def download(session: aiohttp.ClientSession, url: str, limit: int) -> bytes:
    """Body of a URL, refusing more than `limit` bytes. Raises PackError."""
    try:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT_S)
        ) as response:
            if response.status != 200:
                raise PackError(f"{url}: HTTP {response.status}")
            body = bytearray()
            async for chunk in response.content.iter_chunked(64 * 1024):
                body += chunk
                if len(body) > limit:
                    raise PackError(f"{url}: more than {limit} bytes")
            return bytes(body)
    except (aiohttp.ClientError, TimeoutError) as err:
        raise PackError(f"{url}: {err}") from err


class PackClient:
    """Reads the releases of the catalog repository."""

    def __init__(self, session: aiohttp.ClientSession, repo: str) -> None:
        """Bind to a `owner/name` GitHub repository."""
        self._session = session
        self.base_url = f"https://github.com/{repo}/releases"

    def release_url(self, version: str) -> str:
        """Page of a release."""
        return f"{self.base_url}/tag/{version}"

    async def latest(self) -> Manifest:
        """Manifest of the latest release."""
        blob = await download(
            self._session,
            f"{self.base_url}/latest/download/{MANIFEST_FILE}",
            MAX_MANIFEST_BYTES,
        )
        try:
            return parse_manifest(json.loads(blob.decode("utf-8")))
        except (UnicodeDecodeError, ValueError) as err:
            raise PackError(f"unreadable manifest: {err}") from err

    async def entry(self, manifest: Manifest, entry: PackEntry) -> bytes:
        """Checked archive of an entry."""
        blob = await download(
            self._session,
            f"{self.base_url}/download/{manifest.version}/{entry.file}",
            entry.size,
        )
        verify(blob, entry)
        return blob


ProgressCallback = Callable[[int], None]
