"""Atlas building: the coral mask encoding the card relies on."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
build_atlas = importlib.import_module("build_atlas")


def test_split_coral_weights() -> None:
    sheet = Image.new("RGBA", (5, 1))
    sheet.putpixel((0, 0), (255, 0, 0, 255))  # pure colour 1
    sheet.putpixel((1, 0), (0, 128, 0, 255))  # colour 2, darker
    sheet.putpixel((2, 0), (128, 128, 128, 255))  # grey: colour 4
    sheet.putpixel((3, 0), (255, 255, 0, 255))  # half 1, half 2
    sheet.putpixel((4, 0), (0, 0, 0, 0))  # transparent
    shade, mask = build_atlas.split_coral(sheet)
    assert shade.getpixel((1, 0))[:3] == (128, 128, 128)
    assert mask.getpixel((0, 0)) == (255, 0, 0, 255)
    assert mask.getpixel((1, 0)) == (0, 255, 0, 255)
    assert mask.getpixel((2, 0)) == (0, 0, 0, 255)
    r, g, b, _ = mask.getpixel((3, 0))
    assert abs(r - 128) <= 4 and abs(g - 128) <= 4 and b == 0
    assert mask.getpixel((4, 0))[3] == 0


def test_build_atlas_layout() -> None:
    frames = [Image.new("RGBA", (10, 5), (255, 0, 0, 255)) for _ in range(5)]
    clips = [
        build_atlas.Clip("swim", frames[:3], 24, True),
        build_atlas.Clip("turn", frames[3:], 12, False),
    ]
    atlas = build_atlas.build_atlas(clips, (10, 5), columns=2)
    assert atlas.sheet.size == (20, 15)
    assert atlas.clips == {
        "swim": {"from": 0, "to": 2, "fps": 24, "loop": True},
        "turn": {"from": 3, "to": 4, "fps": 12, "loop": False},
    }


def test_parse_clip() -> None:
    assert build_atlas.parse_clip("swim=a.png") == ("swim", Path("a.png"), 24, None)
    assert build_atlas.parse_clip("turn=b:12:loop") == ("turn", Path("b"), 12, True)
    with pytest.raises(SystemExit):
        build_atlas.parse_clip("nope")


def test_cli_writes_fish_entry(tmp_path: Path) -> None:
    frames = tmp_path / "frames"
    frames.mkdir()
    for n in range(4):
        image = Image.new("RGBA", (40, 20), (0, 0, 0, 0))
        image.paste((0, 200, 180, 255), (5 + n, 5, 30 + n, 15))
        image.save(frames / f"{n:03d}.png")
    meta = tmp_path / "meta.json"
    meta.write_text(json.dumps({"size_cm": [5, 8]}), encoding="utf-8")
    out = tmp_path / "out"
    assert (
        build_atlas.main(
            [
                "fish",
                "test_fish",
                "--clip",
                f"swim={frames}",
                "--meta",
                str(meta),
                "--out",
                str(out),
                "--frame",
                "32x16",
            ]
        )
        == 0
    )
    desc = json.loads((out / "test_fish" / "species.json").read_text(encoding="utf-8"))
    assert desc["atlas"] == {"1x": "test_fish.webp"}
    assert desc["clips"]["swim"] == {"from": 0, "to": 3, "fps": 24, "loop": True}
    assert desc["size_cm"] == [5, 8]
    assert Image.open(out / "test_fish" / "test_fish.webp").size == (128, 16)
