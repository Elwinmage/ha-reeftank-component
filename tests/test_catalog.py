"""Asset catalog: scanning, URL resolution and merging."""

from __future__ import annotations

import json
from pathlib import Path

from custom_components.reeftank import BUNDLED_CATALOG
from custom_components.reeftank.catalog import load_catalog, scan_catalog


def _write(root: Path, kind: str, entry_id: str, name: str, content: str) -> None:
    folder = root / kind / entry_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(content, encoding="utf-8")


def test_bundled_demo_entries() -> None:
    catalog = scan_catalog(BUNDLED_CATALOG, "/b", "bundled")
    fish = catalog["fish"]["demo_damselfish"]
    assert fish["source"] == "bundled"
    assert fish["atlas"]["1x"] == "/b/fish/demo_damselfish/demo_damselfish.webp"
    assert fish["clips"]["swim"]["loop"] is True
    coral = catalog["corals"]["demo_euphyllia"]
    assert coral["atlas"]["mask"] == "/b/corals/demo_euphyllia/demo_euphyllia.mask.png"
    assert len(coral["palette"]) == 4
    # Every asset a descriptor names exists
    for kind, entries in catalog.items():
        for entry_id, entry in entries.items():
            for url in entry.get("atlas", {}).values():
                file = url.split("/")[-1]
                assert (BUNDLED_CATALOG / kind / entry_id / file).is_file()


def test_scan_skips_bad_entries(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "fish",
        "good",
        "species.json",
        json.dumps(
            {"atlas": {"1x": "g.webp", "x": "../bad", "n": 3}, "thumbnail": "t.webp"}
        ),
    )
    _write(tmp_path, "fish", "broken", "species.json", "{not json")
    _write(tmp_path, "fish", "listy", "species.json", "[1, 2]")
    _write(tmp_path, "fish", "Bad Name", "species.json", "{}")
    _write(tmp_path, "fish", "nodesc", "other.json", "{}")
    (tmp_path / "fish" / "loose.json").write_text("{}", encoding="utf-8")
    _write(
        tmp_path,
        "presets",
        "reefer",
        "preset.json",
        json.dumps({"views": {"front": {"image": "front.webp"}, "x": 3}}),
    )
    catalog = scan_catalog(tmp_path, "/u", "user")
    assert list(catalog["fish"]) == ["good"]
    good = catalog["fish"]["good"]
    assert good["atlas"] == {"1x": "/u/fish/good/g.webp", "x": "../bad", "n": 3}
    assert good["thumbnail"] == "/u/fish/good/t.webp"
    assert (
        catalog["presets"]["reefer"]["views"]["front"]["image"]
        == "/u/presets/reefer/front.webp"
    )
    assert catalog["corals"] == {}


def test_missing_root(tmp_path: Path) -> None:
    assert scan_catalog(tmp_path / "nope", "/u", "user") == {
        "fish": {},
        "corals": {},
        "presets": {},
    }


def test_user_entries_override_bundled(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "fish",
        "demo_damselfish",
        "species.json",
        json.dumps({"size_cm": [1, 2]}),
    )
    _write(tmp_path, "fish", "aaa_first", "species.json", "{}")
    merged = load_catalog(BUNDLED_CATALOG, "/b", tmp_path, "/u")
    ids = [e["id"] for e in merged["fish"]]
    assert ids == sorted(ids)
    demo = next(e for e in merged["fish"] if e["id"] == "demo_damselfish")
    assert demo["source"] == "user" and demo["size_cm"] == [1, 2]
    assert any(e["id"] == "demo_euphyllia" for e in merged["corals"])
