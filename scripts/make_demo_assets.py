#!/usr/bin/env python3
"""Generate the demo species of the bundled catalog.

They are drawn procedurally, so the whole pipeline (atlas, descriptor, card
rendering, coral recolouring) can be exercised before real clips exist:

- `demo_damselfish`: a small blue-green fish (swim, turn and idle clips);
- `demo_euphyllia`: a coral painted in the R/G/B convention of
  build_atlas.py (day, close and night clips).

    python scripts/make_demo_assets.py

Requires Pillow and numpy.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
from build_atlas import Clip, write_entry

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "custom_components" / "reeftank" / "catalog"

SS = 2  # supersampling factor


def _fish_frame(phase: float, squash: float = 1.0, speed: float = 1.0) -> Image.Image:
    """One frame of the demo fish, facing right.

    phase: tail beat phase (radians); squash: horizontal scale (turning).
    """
    w, h = 512 * SS, 256 * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = w * 0.52, h * 0.5
    body_l, body_h = w * 0.30, h * 0.26

    def x(px: float) -> float:
        return cx + (px - cx) * squash

    beat = math.sin(phase) * 0.35 * speed
    # Tail: a triangle swinging around the caudal peduncle
    base = (cx - body_l * 0.95, cy)
    tip_up = (cx - body_l * 1.55, cy - body_h * 0.75 + beat * body_h)
    tip_down = (cx - body_l * 1.55, cy + body_h * 0.75 + beat * body_h)
    d.polygon(
        [
            (x(base[0]), base[1]),
            (x(tip_up[0]), tip_up[1]),
            (x(tip_down[0]), tip_down[1]),
        ],
        fill=(40, 170, 160, 235),
    )
    # Dorsal and anal fins
    d.polygon(
        [
            (x(cx - body_l * 0.5), cy - body_h * 0.8),
            (x(cx + body_l * 0.3), cy - body_h * 0.9),
            (x(cx - body_l * 0.2), cy - body_h * 1.25),
        ],
        fill=(50, 190, 175, 230),
    )
    d.polygon(
        [
            (x(cx - body_l * 0.4), cy + body_h * 0.8),
            (x(cx + body_l * 0.1), cy + body_h * 0.85),
            (x(cx - body_l * 0.3), cy + body_h * 1.15),
        ],
        fill=(50, 190, 175, 230),
    )
    # Body: stacked ellipses for a simple vertical gradient
    for n, color in enumerate([(30, 140, 150), (60, 200, 190), (150, 235, 220)]):
        k = 1 - n * 0.25
        d.ellipse(
            [
                x(cx - body_l),
                cy - body_h * k,
                x(cx + body_l),
                cy + body_h * k * 0.9 - n * 6 * SS,
            ],
            fill=(*color, 255),
        )
    # Pectoral fin, beating faster
    pec = math.sin(phase * 2) * 0.3
    d.polygon(
        [
            (x(cx + body_l * 0.25), cy),
            (x(cx - body_l * 0.15), cy + body_h * (0.35 + pec)),
            (x(cx - body_l * 0.05), cy - body_h * 0.05),
        ],
        fill=(120, 230, 215, 200),
    )
    # Eye
    ex, ey, er = x(cx + body_l * 0.62), cy - body_h * 0.18, body_h * 0.16
    d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(250, 250, 250, 255))
    d.ellipse(
        [ex - er * 0.55, ey - er * 0.55, ex + er * 0.55, ey + er * 0.55],
        fill=(10, 10, 20, 255),
    )
    img = img.filter(ImageFilter.GaussianBlur(SS * 0.6))
    return img.resize((w // SS, h // SS), Image.Resampling.LANCZOS)


def make_fish() -> None:
    swim = [_fish_frame(2 * math.pi * n / 24) for n in range(24)]
    # Turn: the body narrows to its edge then widens back, mirrored by the
    # card from the half-way frame.
    turn = [_fish_frame(0.0, max(0.08, math.cos(math.pi * n / 7))) for n in range(8)]
    idle = [_fish_frame(2 * math.pi * n / 12, speed=0.35) for n in range(12)]
    write_entry(
        "fish",
        "demo_damselfish",
        [
            Clip("swim", swim, 24, True),
            Clip("turn", turn, 24, False),
            Clip("idle", idle, 12, True),
        ],
        CATALOG / "fish",
        (256, 128),
        8,
        {
            "demo": True,
            "facing": "right",
            "size_cm": [5, 8],
            "behavior": {
                "profile": "shoal",
                "depth": [0.15, 0.85],
                "band": [0.1, 0.7],
                "speed_cm_s": [4, 12],
                "turn_rate": 2.5,
                "shoal": {"cohesion": 1.0, "alignment": 0.8, "separation": 1.2},
            },
            "night": "hide",
            "feeding_response": 0.9,
            "names": {
                "en": "Demo damselfish",
                "fr": "Demoiselle (démo)",
                "de": "Riffbarsch (Demo)",
                "es": "Damisela (demo)",
                "it": "Castagnola (demo)",
                "nl": "Juffertje (demo)",
                "pl": "Garbik (demo)",
                "pt": "Donzela (demo)",
            },
        },
    )


def _coral_frame(t: float, opening: float) -> Image.Image:
    """One frame of the demo coral.

    t: sway phase (radians); opening: 1 fully open, 0 closed.
    Zones: stalk grey (colour 4), tentacles pure green (colour 2),
    tips pure blue (colour 3), mouth pure red (colour 1).
    """
    w = h = 256 * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    base_y = h * 0.95
    # Stalk (grey: takes colour 4)
    d.polygon(
        [
            (w * 0.40, base_y),
            (w * 0.60, base_y),
            (w * 0.56, h * 0.62),
            (w * 0.44, h * 0.62),
        ],
        fill=(150, 150, 150, 255),
    )
    count = 9
    for n in range(count):
        angle = (
            -math.pi / 2 + (n - (count - 1) / 2) * 0.28 + math.sin(t + n * 0.7) * 0.12
        )
        length = h * (0.18 + 0.22 * opening) * (0.85 + 0.15 * math.sin(n * 1.7))
        x0, y0 = w * 0.5 + (n - (count - 1) / 2) * w * 0.012, h * 0.63
        segments = 8
        points = []
        for s in range(segments + 1):
            k = s / segments
            bend = math.sin(t + n * 0.7 + k * 2) * 0.25 * k
            points.append(
                (
                    x0 + math.cos(angle + bend) * length * k,
                    y0 + math.sin(angle + bend) * length * k,
                )
            )
        width = int(w * 0.035)
        for s in range(segments):
            shade = int(150 + 105 * (s / segments))
            d.line([points[s], points[s + 1]], fill=(0, shade, 0, 255), width=width)
        tx, ty = points[-1]
        r = w * (0.022 + 0.012 * opening)
        d.ellipse([tx - r, ty - r, tx + r, ty + r], fill=(0, 0, 230, 255))
    # Mouth (pure red: colour 1)
    d.ellipse([w * 0.46, h * 0.60, w * 0.54, h * 0.66], fill=(220, 0, 0, 255))
    img = img.filter(ImageFilter.GaussianBlur(SS * 0.5))
    return img.resize((w // SS, h // SS), Image.Resampling.LANCZOS)


def make_coral() -> None:
    day = [_coral_frame(2 * math.pi * n / 24, 1.0) for n in range(24)]
    close = [_coral_frame(0.0, 1 - n / 11) for n in range(12)]
    night = [_coral_frame(2 * math.pi * n / 8, 0.0) for n in range(8)]
    write_entry(
        "coral",
        "demo_euphyllia",
        [
            Clip("day", day, 12, True),
            Clip("close", close, 12, False),
            Clip("night", night, 6, True),
        ],
        CATALOG / "corals",
        (256, 256),
        8,
        {
            "demo": True,
            "size_cm": [5, 25],
            "palette": [
                {"default": "#8a3b2e", "fluo": False},
                {"default": "#3fae5a", "fluo": False},
                {"default": "#3aa0ff", "fluo": True},
                {"default": "#9a8f7a", "fluo": False},
            ],
            "names": {
                "en": "Demo euphyllia",
                "fr": "Euphyllia (démo)",
                "de": "Euphyllia (Demo)",
                "es": "Euphyllia (demo)",
                "it": "Euphyllia (demo)",
                "nl": "Euphyllia (demo)",
                "pl": "Euphyllia (demo)",
                "pt": "Euphyllia (demo)",
            },
        },
    )


if __name__ == "__main__":
    make_fish()
    make_coral()
    print(f"demo assets written under {CATALOG}")
