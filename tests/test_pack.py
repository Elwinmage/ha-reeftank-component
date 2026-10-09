"""Downloaded catalog: manifests, archives, staging."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from release import entry_zip, release, species

from custom_components.reeftank import pack
from custom_components.reeftank.pack import PackError, parse_manifest


def _manifest(**overrides: Any) -> dict[str, Any]:
    manifest, _ = release("2026.10.0", {"fish/siganus": species("siganus")})
    manifest.update(overrides)
    return manifest


def test_parse_manifest() -> None:
    parsed = parse_manifest(_manifest(min_integration="0.1.0"))
    assert parsed.version == "2026.10.0"
    assert parsed.min_integration == "0.1.0"
    item = parsed.entries["fish/siganus"]
    assert (item.kind, item.entry_id) == ("fish", "siganus")


def test_textures_install(tmp_path: Path) -> None:
    files = {"texture.json": json.dumps({"role": "rock"}), "rock.webp": b"RIFF"}
    manifest, blobs = release("1", {"textures/rock": files})
    parsed = parse_manifest(manifest)
    item = parsed.entries["textures/rock"]
    assert item.kind == "textures"
    pack.extract_entry(blobs[item.file], item.kind, tmp_path / "rock")
    assert (tmp_path / "rock" / "texture.json").is_file()
    with pytest.raises(PackError, match="no texture.json"):
        pack.extract_entry(
            entry_zip({"species.json": "{}"}), "textures", tmp_path / "x"
        )


@pytest.mark.parametrize(
    "bad",
    [
        [],
        {"format": 2},
        _manifest(version="x y"),
        _manifest(min_integration=3),
        _manifest(notes=[]),
        _manifest(entries=[]),
        _manifest(entries={"plants/x": {}}),
        _manifest(entries={"fish/Bad": {}}),
        _manifest(entries={"fish/x": []}),
        _manifest(entries={"fish/x": {"sha256": "zz", "size": 1, "file": "a.zip"}}),
        _manifest(entries={"fish/x": {"sha256": "0" * 64, "size": 0, "file": "a.zip"}}),
        _manifest(entries={"fish/x": {"sha256": "0" * 64, "size": 1, "file": "../a"}}),
        _manifest(
            entries={
                "fish/x": {"sha256": "0" * 64, "size": 1, "file": "a.zip", "version": 1}
            }
        ),
    ],
)
def test_bad_manifests(bad: Any) -> None:
    with pytest.raises(PackError):
        parse_manifest(bad)


def test_compatibility() -> None:
    assert pack.is_compatible(parse_manifest(_manifest()), "v0.1.0")
    needs = parse_manifest(_manifest(min_integration="0.3.0"))
    assert not pack.is_compatible(needs, "v0.2.9")
    assert pack.is_compatible(needs, "0.3.0")


def test_plan_and_verify() -> None:
    old, _ = release("1", {"fish/a": species("a"), "fish/b": species("b")})
    new, blobs = release(
        "2", {"fish/a": species("a"), "fish/b": species("b", size_cm=[2, 3])}
    )
    keep, fetch = pack.plan(parse_manifest(old), parse_manifest(new))
    assert [e.key for e in keep] == ["fish/a"]
    assert [e.key for e in fetch] == ["fish/b"]
    assert [e.key for e in pack.plan(None, parse_manifest(new))[1]] == [
        "fish/a",
        "fish/b",
    ]
    entry = parse_manifest(new).entries["fish/b"]
    pack.verify(blobs["fish-b.zip"], entry)
    with pytest.raises(PackError, match="bytes"):
        pack.verify(blobs["fish-b.zip"] + b"x", entry)
    with pytest.raises(PackError, match="checksum"):
        pack.verify(
            blobs["fish-a.zip"][:-1] + b"#", parse_manifest(new).entries["fish/a"]
        )


@pytest.mark.parametrize(
    ("files", "message"),
    [
        ({}, "0 files"),
        ({f"f{i}.png": b"x" for i in range(20)}, "20 files"),
        ({"species.json": "{}", "../evil.json": "{}"}, "unexpected"),
        ({"species.json": "{}", "sub/a.webp": b"x"}, "unexpected"),
        ({"species.json": "{}", "run.sh": "x"}, "unexpected"),
        ({"a.webp": b"x"}, "no species.json"),
        ({"species.json": "{oops"}, "unreadable"),
        ({"species.json": b"\xff\xfe"}, "unreadable"),
        ({"species.json": "[1]"}, "not an object"),
    ],
)
def test_bad_archives(tmp_path: Path, files: dict[str, Any], message: str) -> None:
    with pytest.raises(PackError, match=message):
        pack.extract_entry(entry_zip(files), "fish", tmp_path / "x")


def test_archive_limits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(PackError, match="not a zip"):
        pack.extract_entry(b"nope", "fish", tmp_path / "x")
    monkeypatch.setattr(pack, "MAX_ENTRY_BYTES", 10)
    with pytest.raises(PackError, match="too big"):
        pack.extract_entry(entry_zip(species("x")), "fish", tmp_path / "x")


def test_stage_and_commit(tmp_path: Path) -> None:
    root = tmp_path / "pack"
    first, blobs = release(
        "1", {"fish/a": species("a"), "corals/c": {"species.json": "{}"}}
    )
    parsed = parse_manifest(first)
    staging = pack.prepare_staging(root, [])
    for item in parsed.entries.values():
        pack.extract_entry(
            blobs[item.file], item.kind, staging / item.kind / item.entry_id
        )
    pack.commit(root, staging, parsed)
    assert (root / "fish" / "a" / "thumb.webp").is_file()
    installed = pack.read_installed(root)
    assert installed is not None and installed.version == "1"

    # second release: one kept, one gone
    second, _ = release("2", {"fish/a": species("a")})
    keep, fetch = pack.plan(installed, parse_manifest(second))
    assert len(keep) == 1 and not fetch
    staging = pack.prepare_staging(root, keep)
    pack.commit(root, staging, parse_manifest(second))
    assert not (root / "corals").exists()
    assert not pack.staging_dir(root).exists()
    assert not root.with_name("pack.old").exists()

    # a missing folder means "not installed"
    (root / "fish" / "a" / "species.json").unlink()
    assert pack.read_installed(root) is None
    (root / "manifest.json").write_text("{", encoding="utf-8")
    assert pack.read_installed(root) is None
    assert pack.read_installed(tmp_path / "none") is None
    # a pack folder missing altogether is created
    pack.commit(
        tmp_path / "fresh",
        pack.prepare_staging(tmp_path / "fresh", []),
        parse_manifest(second),
    )
    assert (
        json.loads((tmp_path / "fresh" / "manifest.json").read_text())["version"] == "2"
    )
