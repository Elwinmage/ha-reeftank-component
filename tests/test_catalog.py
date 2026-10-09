"""Asset catalog: scanning, URL resolution and merging."""

from __future__ import annotations

import json
from pathlib import Path

from custom_components.reeftank.catalog import load_catalog, scan_catalog


def _write(root: Path, kind: str, entry_id: str, name: str, content: str) -> None:
    folder = root / kind / entry_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(content, encoding="utf-8")


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
    _write(
        tmp_path,
        "textures",
        "live_rock",
        "texture.json",
        json.dumps({"role": "rock", "image": "live_rock.webp", "scale_cm": 30}),
    )
    catalog = scan_catalog(tmp_path, "/u", "user")
    assert catalog["textures"]["live_rock"]["image"] == (
        "/u/textures/live_rock/live_rock.webp"
    )
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
        "textures": {},
        "presets": {},
    }


def test_user_entries_override_pack(tmp_path: Path) -> None:
    pack = tmp_path / "pack"
    user = tmp_path / "user"
    _write(pack, "fish", "siganus", "species.json", json.dumps({"size_cm": [15, 22]}))
    _write(pack, "corals", "euphyllia", "species.json", json.dumps({"palette": []}))
    _write(user, "fish", "siganus", "species.json", json.dumps({"size_cm": [1, 2]}))
    _write(user, "fish", "aaa_first", "species.json", "{}")
    merged = load_catalog(pack, "/p", user, "/u")
    assert [e["id"] for e in merged["fish"]] == ["aaa_first", "siganus"]
    siganus = merged["fish"][1]
    assert siganus["source"] == "user" and siganus["size_cm"] == [1, 2]
    assert merged["corals"][0]["source"] == "pack"
