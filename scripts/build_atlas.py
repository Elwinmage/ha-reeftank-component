#!/usr/bin/env python3
"""Build a sprite atlas and its descriptor from animation frames.

The card does not play videos: it draws frames out of an atlas (one picture,
frames on a grid), so every fish has its own phase and a tail beat following
its speed. This script turns source clips into that atlas.

Source clips can be:
- a folder of PNG frames (with alpha), played in name order;
- any file ffmpeg reads (APNG, MOV with alpha, WebM...), when ffmpeg is
  installed.

Fish
----

    build_atlas.py fish chromis_viridis \
        --clip swim=clips/chromis_swim.apng \
        --clip turn=clips/chromis_turn.apng \
        --meta clips/chromis.meta.json \
        --out custom_components/reeftank/catalog/fish

writes <out>/chromis_viridis/{species.json, chromis_viridis.webp,
chromis_viridis@2x.webp}.

Corals
------

A coral is drawn with its zones painted in **pure red, pure green and pure
blue**, shaded as wanted; grey parts take the fourth colour. From that one
clip the script derives:

- `<id>.shade.webp`: the shading (brightness of every pixel);
- `<id>.mask.png`: lossless, R/G/B = weight of palette colours 1/2/3, the
  fourth colour gets what is left.

The card recolours the coral with the user's palette:
`pixel = shade x (w1.c1 + w2.c2 + w3.c3 + (1 - w1 - w2 - w3).c4)`.

    build_atlas.py coral euphyllia_glabrescens \
        --clip day=clips/euphyllia_day --clip close=clips/euphyllia_close \
        --clip night=clips/euphyllia_night --meta clips/euphyllia.meta.json \
        --out custom_components/reeftank/catalog/corals

Clips
-----

`--clip name=source[:fps[:loop]]`. Defaults: 24 fps, `swim`, `idle`, `day`
and `night` loop, the others play once. The meta file (JSON) is merged into
the descriptor: size_cm, behavior, night, feeding_response, palette, names...

Requires Pillow and numpy.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

LOOPING = {"swim", "idle", "day", "night"}
DEFAULT_FPS = 24


@dataclass
class Clip:
    """A named sequence of frames."""

    name: str
    frames: list[Image.Image]
    fps: int = DEFAULT_FPS
    loop: bool = False


@dataclass
class Atlas:
    """Frames laid out on a grid, with the clips indexing them."""

    frame: tuple[int, int]
    columns: int
    sheet: Image.Image
    clips: dict[str, dict[str, Any]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Reading sources
# ---------------------------------------------------------------------------


def read_frames(source: Path) -> list[Image.Image]:
    """Frames of a clip: a folder of PNG files, or a file ffmpeg can read."""
    if source.is_dir():
        files = sorted(p for p in source.iterdir() if p.suffix.lower() == ".png")
        if not files:
            raise SystemExit(f"no PNG frame in {source}")
        return [Image.open(p).convert("RGBA") for p in files]

    # An animated picture Pillow understands natively (APNG, animated WebP)
    try:
        image = Image.open(source)
        n_frames = int(getattr(image, "n_frames", 1))
        if n_frames > 1:
            frames = []
            for index in range(n_frames):
                image.seek(index)
                frames.append(image.convert("RGBA"))
            return frames
    except OSError:
        pass

    if shutil.which("ffmpeg") is None:
        raise SystemExit(f"cannot read {source}: install ffmpeg or give PNG frames")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-i",
                str(source),
                "-pix_fmt",
                "rgba",
                str(Path(tmp) / "f%05d.png"),
            ],
            check=True,
        )
        return read_frames(Path(tmp))


def parse_clip(spec: str) -> tuple[str, Path, int, bool | None]:
    """Parse `name=source[:fps[:loop]]`."""
    if "=" not in spec:
        raise SystemExit(f"bad --clip {spec!r}: expected name=source")
    name, rest = spec.split("=", 1)
    parts = rest.split(":")
    source = Path(parts[0])
    fps = int(parts[1]) if len(parts) > 1 and parts[1] else DEFAULT_FPS
    loop: bool | None = None
    if len(parts) > 2 and parts[2]:
        loop = parts[2].lower() in ("1", "true", "loop", "yes")
    return name, source, fps, loop


# ---------------------------------------------------------------------------
# Building
# ---------------------------------------------------------------------------


def common_box(frames: list[Image.Image]) -> tuple[int, int, int, int]:
    """Smallest box holding the visible part of every frame."""
    boxes = [f.getchannel("A").getbbox() for f in frames]
    boxes = [b for b in boxes if b]
    if not boxes:
        width, height = frames[0].size
        return (0, 0, width, height)
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def fit(frames: list[Image.Image], size: tuple[int, int]) -> list[Image.Image]:
    """Crop frames to their common visible box and fit them into `size`."""
    box = common_box(frames)
    out = []
    for frame in frames:
        cropped = frame.crop(box)
        scale = min(size[0] / cropped.width, size[1] / cropped.height)
        resized = cropped.resize(
            (
                max(1, round(cropped.width * scale)),
                max(1, round(cropped.height * scale)),
            ),
            Image.Resampling.LANCZOS,
        )
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        canvas.paste(
            resized,
            ((size[0] - resized.width) // 2, (size[1] - resized.height) // 2),
        )
        out.append(canvas)
    return out


def build_atlas(clips: list[Clip], frame: tuple[int, int], columns: int = 8) -> Atlas:
    """Lay the frames of every clip on one grid."""
    all_frames: list[Image.Image] = []
    index: dict[str, dict[str, Any]] = {}
    for clip in clips:
        start = len(all_frames)
        all_frames += clip.frames
        index[clip.name] = {
            "from": start,
            "to": len(all_frames) - 1,
            "fps": clip.fps,
            "loop": clip.loop,
        }
    columns = max(1, min(columns, len(all_frames)))
    rows = math.ceil(len(all_frames) / columns)
    sheet = Image.new("RGBA", (frame[0] * columns, frame[1] * rows), (0, 0, 0, 0))
    for n, image in enumerate(all_frames):
        sheet.paste(image, ((n % columns) * frame[0], (n // columns) * frame[1]))
    return Atlas(frame=frame, columns=columns, sheet=sheet, clips=index)


def split_coral(sheet: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Split a coral sheet painted in pure R/G/B/grey into shade and mask.

    shade: brightness (max channel) + alpha.
    mask:  R/G/B = weights of palette colours 1/2/3 (saturated parts), the
           grey part (1 - saturation) goes to colour 4.
    """
    rgba = np.asarray(sheet.convert("RGBA")).astype(np.float32) / 255.0
    rgb, alpha = rgba[..., :3], rgba[..., 3]
    value = rgb.max(axis=-1)
    low = rgb.min(axis=-1)
    chroma = value - low
    saturation = np.where(value > 1e-6, chroma / np.maximum(value, 1e-6), 0.0)
    excess = rgb - low[..., None]
    total = excess.sum(axis=-1)
    weights = np.where(
        total[..., None] > 1e-6,
        excess / np.maximum(total, 1e-6)[..., None] * saturation[..., None],
        0.0,
    )

    shade = np.dstack([value, value, value, alpha])
    # 32 weight levels are plenty for a colour mix, and compress far better
    weights = np.round(weights * 32) / 32
    mask = np.dstack([weights, np.where(alpha > 0.02, 1.0, 0.0)])
    to_img = lambda a: Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))
    return to_img(shade), to_img(mask)


def save_webp(image: Image.Image, path: Path) -> None:
    """Lossy WebP keeping a clean alpha."""
    image.save(path, format="WEBP", quality=80, alpha_quality=90, method=6)


def write_entry(
    kind: str,
    entry_id: str,
    clips: list[Clip],
    out: Path,
    frame: tuple[int, int],
    columns: int,
    meta: dict[str, Any],
    hd: bool = False,
) -> Path:
    """Write the atlas pictures and the descriptor of a catalog entry.

    hd: also write a double resolution atlas (for very large sprites).
    """
    folder = out / entry_id
    folder.mkdir(parents=True, exist_ok=True)
    big = (frame[0] * 2, frame[1] * 2)
    atlas_2x = (
        build_atlas(
            [Clip(c.name, fit(c.frames, big), c.fps, c.loop) for c in clips],
            big,
            columns,
        )
        if hd
        else None
    )
    atlas_1x = build_atlas(
        [Clip(c.name, fit(c.frames, frame), c.fps, c.loop) for c in clips],
        frame,
        columns,
    )

    descriptor: dict[str, Any] = {
        "kind": "fish" if kind == "fish" else "coral",
        "frame": list(frame),
        "columns": atlas_1x.columns,
        "clips": atlas_1x.clips,
    }
    if kind == "fish":
        save_webp(atlas_1x.sheet, folder / f"{entry_id}.webp")
        descriptor["atlas"] = {"1x": f"{entry_id}.webp"}
        if atlas_2x is not None:
            save_webp(atlas_2x.sheet, folder / f"{entry_id}@2x.webp")
            descriptor["atlas"]["2x"] = f"{entry_id}@2x.webp"
        descriptor.setdefault("facing", "right")
    else:
        shade, mask = split_coral(atlas_1x.sheet)
        save_webp(shade, folder / f"{entry_id}.shade.webp")
        mask.save(folder / f"{entry_id}.mask.png", optimize=True)
        descriptor["atlas"] = {
            "shade": f"{entry_id}.shade.webp",
            "mask": f"{entry_id}.mask.png",
        }
        if atlas_2x is not None:
            shade2, mask2 = split_coral(atlas_2x.sheet)
            save_webp(shade2, folder / f"{entry_id}.shade@2x.webp")
            mask2.save(folder / f"{entry_id}.mask@2x.png", optimize=True)
            descriptor["atlas"]["shade_2x"] = f"{entry_id}.shade@2x.webp"
            descriptor["atlas"]["mask_2x"] = f"{entry_id}.mask@2x.png"
    descriptor.update(meta)
    (folder / "species.json").write_text(
        json.dumps(descriptor, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return folder


def main(argv: list[str] | None = None) -> int:
    """Command line entry point."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument("kind", choices=["fish", "coral"])
    parser.add_argument("id", help="catalog id (folder name), ex: chromis_viridis")
    parser.add_argument(
        "--clip", action="append", required=True, help="name=source[:fps[:loop]]"
    )
    parser.add_argument("--meta", type=Path, help="JSON merged into the descriptor")
    parser.add_argument(
        "--frame",
        default=None,
        help="frame size WxH (default 256x128 fish, 256x256 coral)",
    )
    parser.add_argument("--columns", type=int, default=8)
    parser.add_argument(
        "--hd", action="store_true", help="also write a double resolution atlas"
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    frame_spec = args.frame or ("256x128" if args.kind == "fish" else "256x256")
    width, height = (int(v) for v in frame_spec.lower().split("x"))

    clips = []
    for spec in args.clip:
        name, source, fps, loop = parse_clip(spec)
        clips.append(
            Clip(
                name,
                read_frames(source),
                fps,
                name in LOOPING if loop is None else loop,
            )
        )
    meta = json.loads(args.meta.read_text(encoding="utf-8")) if args.meta else {}
    folder = write_entry(
        args.kind,
        args.id,
        clips,
        args.out,
        (width, height),
        args.columns,
        meta,
        args.hd,
    )
    print(f"written {folder}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
