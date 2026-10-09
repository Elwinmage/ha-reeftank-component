"""Validation and inventory helpers of the aquarium documents."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from custom_components.reeftank import models
from custom_components.reeftank.compat import vol
from custom_components.reeftank.models import (
    coral_counts,
    feeding_points,
    fish_counts,
    livestock_add,
    livestock_counts,
    livestock_remove,
    referenced_images,
    validate_document,
)


def test_new_id_is_short_hex() -> None:
    value = models.new_id()
    assert len(value) == 8
    int(value, 16)
    assert models.new_id() != value
    # never all digits (an integer key in JavaScript)
    assert all(models.new_id()[0] in "abcdef" for _ in range(200))


def test_valid_document_gets_defaults(document: dict[str, Any]) -> None:
    original = deepcopy(document)
    doc = validate_document(document)
    assert document == original, "input must not be modified"
    assert doc["version"] == 1
    assert doc["revision"] == 0
    assert doc["photo_light"] == "white"
    assert doc["render"] == {"level": "full", "max_fish": 30, "caustics": False}
    assert doc["default_view"] == "front"
    main = doc["waters"]["main"]
    assert main["sand_band"] == 0.12
    # size range sorted
    assert main["livestock"][0]["size_cm"] == [5.0, 8.0]
    assert main["livestock"][1]["kind"] == "fish"
    # colours lowered
    assert main["corals"][0]["palette"] == ["#5c2d91", "#9be564"]
    assert doc["waters"]["sump"]["lights"][0]["x"] == 0.5
    assert doc["feeding"]["dedup_s"] == 120
    assert doc["feeding"]["duration_s"] == 45
    assert doc["views"]["cabinet"]["regions"][0]["quad"] == []
    assert doc["views"]["cabinet"]["regions"][0]["sand"] == []
    assert doc["views"]["cabinet"]["regions"][0]["drawn"] is False
    assert doc["views"]["cabinet"]["regions"][0]["sand_back"] == []
    assert doc["views"]["front"]["backdrop"] == {"mode": "photo"}
    assert "home" not in main["livestock"][0]


def test_sand_line_home_and_backdrop() -> None:
    doc = validate_document(
        {
            "name": "T",
            "waters": {
                "main": {"livestock": [{"species": "goby", "home": [0.2, 1.4, "0.5"]}]}
            },
            "views": {
                "front": {
                    "regions": [
                        {
                            "water": "main",
                            "sand": [[0.9, 0.8], [0.1, 0.85], [0.5, 0.75]],
                            "sand_back": [[0.8, 0.6], [0.2, 0.62]],
                            "drawn": True,
                        }
                    ],
                    "backdrop": {"mode": "drawn", "rock": "live_rock", "sand": None},
                }
            },
        }
    )
    # points sorted left to right, clamped
    region = doc["views"]["front"]["regions"][0]
    assert region["sand"] == [[0.1, 0.85], [0.5, 0.75], [0.9, 0.8]]
    assert region["drawn"] is True
    assert region["sand_back"] == [[0.2, 0.62], [0.8, 0.6]]
    assert doc["waters"]["main"]["livestock"][0]["home"] == [0.2, 1.0, 0.5]
    assert doc["views"]["front"]["backdrop"]["mode"] == "drawn"
    for bad in (
        {"regions": [{"water": "main", "sand": [[0, 0]]}]},
        {"regions": [{"water": "main", "sand": [[0, 0]] * 33}]},
        {"regions": [{"water": "main", "drawn": "yes"}]},
        {"backdrop": {"mode": "painted"}},
        {"backdrop": {"rock": "Bad Id"}},
    ):
        with pytest.raises(vol.Invalid):
            validate_document(
                {"name": "T", "waters": {"main": {}}, "views": {"v": bad}}
            )
    for home in ([0, 0], "here", [0, 0, "x"]):
        with pytest.raises(vol.Invalid):
            validate_document(
                {
                    "name": "T",
                    "waters": {"main": {"livestock": [{"species": "a", "home": home}]}},
                }
            )


def test_minimal_document() -> None:
    doc = validate_document({"name": "  Nano  "})
    assert doc["name"] == "Nano"
    assert doc["views"] == {}
    assert "default_view" not in doc or doc["default_view"] is None


def test_missing_item_ids_are_generated() -> None:
    doc = validate_document(
        {
            "name": "T",
            "waters": {"main": {"livestock": [{"species": "a"}, {"species": "b"}]}},
        }
    )
    ids = [line["id"] for line in doc["waters"]["main"]["livestock"]]
    assert all(ids) and ids[0] != ids[1]


@pytest.mark.parametrize(
    ("value", "expected"),
    [([-1, 2], [0.0, 1.0]), (["0.5", 0.25], [0.5, 0.25])],
)
def test_points_are_clamped(value: list[Any], expected: list[float]) -> None:
    assert models._point(value) == expected


@pytest.mark.parametrize("value", [[1], "ab", [None, 1], [float("nan"), 0]])
def test_invalid_points(value: Any) -> None:
    with pytest.raises(vol.Invalid):
        models._point(value)


@pytest.mark.parametrize("value", ["", "UPPER", "a b", 12, "x" * 41])
def test_invalid_ids(value: Any) -> None:
    with pytest.raises(vol.Invalid):
        models._ident(value)


def test_quad_and_polygon_sizes() -> None:
    assert models._quad([]) == []
    with pytest.raises(vol.Invalid):
        models._quad([[0, 0], [1, 1]])
    with pytest.raises(vol.Invalid):
        models._polygon([[0, 0], [1, 1]])
    with pytest.raises(vol.Invalid):
        models._polygon("nope")


def test_colours_dates_entities() -> None:
    assert models._hex_color("#ABCDEF") == "#abcdef"
    with pytest.raises(vol.Invalid):
        models._hex_color("red")
    assert models._date("2026-03-14") == "2026-03-14"
    with pytest.raises(vol.Invalid):
        models._date("14/03/2026")
    with pytest.raises(vol.Invalid):
        models._entity_id("Sensor.X")


@pytest.mark.parametrize(
    "value",
    [
        "a1b2/0123abcd.webp",
        "/reeftank/catalog/pack/presets/reefer/front.webp",
        "/reeftank/catalog/user/presets/x/a.webp",
    ],
)
def test_valid_images(value: str) -> None:
    assert models._image(value) == value


def test_empty_image_is_none() -> None:
    assert models._image("") is None
    assert models._image(None) is None


@pytest.mark.parametrize(
    "value",
    [
        "a1b2/x.png",
        "../etc/passwd",
        "/reeftank/catalog/pack/../../secrets.yaml",
        "http://example.com/a.webp",
        12,
    ],
)
def test_invalid_images(value: Any) -> None:
    with pytest.raises(vol.Invalid):
        models._image(value)


def test_size_range_validation() -> None:
    assert models._size_range([3, 2]) == [2.0, 3.0]
    with pytest.raises(vol.Invalid):
        models._size_range([1])


def test_light_needs_a_target() -> None:
    with pytest.raises(vol.Invalid):
        models.LIGHT_SCHEMA({"x": 0.2})


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda d: d.update(default_view="nope"), "default_view"),
        (
            lambda d: d["views"]["front"]["regions"].append({"water": "ghost"}),
            "unknown water",
        ),
        (
            lambda d: d["views"]["front"]["hotspots"][0].update(goto="ghost"),
            "unknown view",
        ),
        (
            lambda d: d["views"]["front"]["elements"].append(
                {"kind": "device", "pos": [0, 0]}
            ),
            "without device_id",
        ),
        (
            lambda d: d["views"]["front"]["elements"].append(
                {"kind": "entity", "pos": [0, 0]}
            ),
            "without entity_id",
        ),
        (
            lambda d: d["views"]["front"]["elements"][1].update(source="ghost"),
            "unknown feeding source",
        ),
        (
            lambda d: d["waters"]["main"]["corals"][0].update(view="ghost"),
            "unknown view",
        ),
        (
            lambda d: d["waters"]["main"]["livestock"][1].update(id="l1"),
            "duplicate id",
        ),
    ],
)
def test_link_errors(document: dict[str, Any], mutate: Any, message: str) -> None:
    mutate(document)
    with pytest.raises(vol.Invalid, match=message):
        validate_document(document)


def test_unknown_keys_are_refused(document: dict[str, Any]) -> None:
    document["views"]["front"]["elements"][0]["bogus"] = 1
    with pytest.raises(vol.Invalid):
        validate_document(document)


def test_counts(document: dict[str, Any]) -> None:
    doc = validate_document(document)
    assert fish_counts(doc) == {"chromis_viridis": 7, "mandarin": 1}
    assert livestock_counts(doc) == {
        "chromis_viridis": 7,
        "cleaner_shrimp": 2,
        "mandarin": 1,
    }
    assert coral_counts(doc) == {"euphyllia": 1}
    doc["waters"]["main"]["livestock"][1]["name"] = "Mandarin dragonet"
    doc["waters"]["main"]["livestock"][0]["count"] = 0
    doc["waters"]["main"]["corals"][0]["name"] = "My euphyllia"
    assert fish_counts(doc) == {"Mandarin dragonet": 1}
    assert coral_counts(doc) == {"My euphyllia": 1}


def test_livestock_add_merges_and_creates(document: dict[str, Any]) -> None:
    doc = validate_document(document)
    line = livestock_add(doc, "main", "chromis_viridis", 3, size_cm=[4, 6], note="new")
    assert line["count"] == 10
    assert line["size_cm"] == [4.0, 6.0]
    assert line["note"] == "new"
    line = livestock_add(doc, "main", "chromis_viridis", 1)
    assert line["count"] == 11
    line = livestock_add(doc, "quarantine", "tang", 1, added="2026-10-08")
    assert line["count"] == 1 and line["added"] == "2026-10-08"
    assert doc["waters"]["quarantine"]["livestock"] == [line]
    validate_document(doc)
    with pytest.raises(vol.Invalid):
        livestock_add(doc, "main", "x", 0)


def test_livestock_remove(document: dict[str, Any]) -> None:
    doc = validate_document(document)
    line = livestock_remove(doc, 2, line_id="l1")
    assert line is not None and line["count"] == 5
    assert livestock_remove(doc, 5, species="mandarin") is None
    assert all(
        line["species"] != "mandarin" for line in doc["waters"]["main"]["livestock"]
    )
    with pytest.raises(KeyError):
        livestock_remove(doc, 1, line_id="ghost")
    with pytest.raises(KeyError):
        livestock_remove(doc, 1)
    with pytest.raises(vol.Invalid):
        livestock_remove(doc, 0, line_id="l1")


def test_referenced_images_and_feeding_points(document: dict[str, Any]) -> None:
    doc = validate_document(document)
    assert referenced_images(doc) == {"a1b2/0123456789abcdef.webp"}
    doc["views"]["cabinet"]["image"] = "/reeftank/catalog/pack/presets/x/a.webp"
    assert referenced_images(doc) == {"a1b2/0123456789abcdef.webp"}
    assert [e["id"] for e in feeding_points(doc)] == ["e2"]
