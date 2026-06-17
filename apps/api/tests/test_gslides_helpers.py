"""Unit tests for Google Slides action node helpers."""

from __future__ import annotations

import pytest

from apps.api.app.node_system.nodes.gslides.gslides_node import (
    GoogleSlidesProperties,
    _color_field,
    _element_kind,
    _extract_element_text,
    _extract_slide_text,
    _gen_object_id,
    _placement,
    _slide_insertion_index,
    _text_range,
)

# ── _color_field ───────────────────────────────────────────────────────


def test_color_field_well_formed_hex():
    assert _color_field("#336699") == {
        "opaqueColor": {
            "rgbColor": {
                "red": 0x33 / 255,
                "green": 0x66 / 255,
                "blue": 0x99 / 255,
            }
        }
    }


def test_color_field_accepts_missing_hash():
    assert _color_field("ff0000") == {
        "opaqueColor": {"rgbColor": {"red": 1.0, "green": 0.0, "blue": 0.0}}
    }


@pytest.mark.parametrize("bad", ["", "abc", "#nothex", "#abc"])
def test_color_field_returns_none_on_invalid(bad):
    assert _color_field(bad) is None


# ── _placement ─────────────────────────────────────────────────────────


def _make_node(**overrides) -> object:
    node = GoogleSlidesProperties(
        credential=None,
        position_x_pt=overrides.get("position_x_pt", 50),
        position_y_pt=overrides.get("position_y_pt", 50),
        width_pt=overrides.get("width_pt", 400),
        height_pt=overrides.get("height_pt", 200),
        insert_position=overrides.get("insert_position", "end"),
        slide_index=overrides.get("slide_index"),
        start_index=overrides.get("start_index"),
        end_index=overrides.get("end_index"),
    )

    class Holder:
        props = node

    return Holder()


def test_placement_builds_size_and_transform_in_pt():
    node = _make_node(position_x_pt=100, position_y_pt=80, width_pt=300, height_pt=150)
    placement = _placement(node, "slide_xyz")
    assert placement["pageObjectId"] == "slide_xyz"
    assert placement["size"]["width"] == {"magnitude": 300.0, "unit": "PT"}
    assert placement["size"]["height"] == {"magnitude": 150.0, "unit": "PT"}
    assert placement["transform"]["translateX"] == 100.0
    assert placement["transform"]["translateY"] == 80.0
    assert placement["transform"]["unit"] == "PT"


# ── _slide_insertion_index ─────────────────────────────────────────────


def test_slide_insertion_index_end_returns_none():
    node = _make_node(insert_position="end")
    assert _slide_insertion_index(node) is None


def test_slide_insertion_index_returns_int_when_explicit():
    node = _make_node(insert_position="index", slide_index=2)
    assert _slide_insertion_index(node) == 2


def test_slide_insertion_index_falls_back_to_zero():
    node = _make_node(insert_position="index", slide_index=None)
    assert _slide_insertion_index(node) == 0


# ── _text_range ────────────────────────────────────────────────────────


def test_text_range_returns_all_by_default():
    node = _make_node()
    assert _text_range(node) == {"type": "ALL"}


def test_text_range_returns_fixed_range_when_set():
    node = _make_node(start_index=10, end_index=42)
    assert _text_range(node) == {
        "type": "FIXED_RANGE",
        "startIndex": 10,
        "endIndex": 42,
    }


# ── _gen_object_id ─────────────────────────────────────────────────────


def test_gen_object_id_starts_with_prefix_and_uses_safe_chars():
    oid = _gen_object_id("tb")
    assert oid.startswith("tb_")
    # Letters + digits + underscores, between 5 and 50 chars.
    assert 5 <= len(oid) <= 50
    assert all(ch.isalnum() or ch in "_-" for ch in oid)


def test_gen_object_id_is_unique_across_calls():
    seen = {_gen_object_id("x") for _ in range(20)}
    assert len(seen) == 20


# ── element-text walking ───────────────────────────────────────────────


def test_extract_element_text_joins_runs():
    element = {
        "shape": {
            "text": {
                "textElements": [
                    {"textRun": {"content": "Hello "}},
                    {"textRun": {"content": "world"}},
                    {"paragraphMarker": {}},  # no textRun → ignored
                    {"textRun": {"content": "!"}},
                ]
            }
        }
    }
    assert _extract_element_text(element) == "Hello world!"


def test_extract_element_text_handles_missing_text():
    assert _extract_element_text({"shape": {}}) == ""
    assert _extract_element_text({"shape": {"text": {}}}) == ""
    assert _extract_element_text({"image": {}}) == ""


def test_element_kind_picks_first_known_key():
    assert _element_kind({"shape": {}}) == "shape"
    assert _element_kind({"image": {}}) == "image"
    assert _element_kind({"table": {}}) == "table"
    assert _element_kind({}) == "unknown"


def test_extract_slide_text_flattens_full_presentation():
    pres = {
        "slides": [
            {
                "objectId": "slide_1",
                "pageElements": [
                    {
                        "objectId": "el_1",
                        "shape": {"text": {"textElements": [{"textRun": {"content": "Title"}}]}},
                    },
                    {
                        "objectId": "el_2",
                        "shape": {"text": {"textElements": [{"textRun": {"content": "Body"}}]}},
                    },
                ],
            },
            {
                "objectId": "slide_2",
                "pageElements": [
                    {
                        "objectId": "el_3",
                        "image": {"contentUrl": "https://x"},
                    }
                ],
            },
        ]
    }
    flat = _extract_slide_text(pres)
    assert flat == [
        {
            "slide_id": "slide_1",
            "text": "Title\nBody",
            "elements": [
                {"id": "el_1", "kind": "shape", "text": "Title"},
                {"id": "el_2", "kind": "shape", "text": "Body"},
            ],
        },
        {
            "slide_id": "slide_2",
            "text": "",
            "elements": [{"id": "el_3", "kind": "image", "text": ""}],
        },
    ]


# ── resource_id coercion ───────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"id": "PRES1", "title": "My Deck"}, "PRES1"),
        ("PRES2", "PRES2"),
        (None, None),
        ("", None),
        ({}, None),
        ({"id": ""}, None),
    ],
)
def test_presentation_id_coercion(raw, expected):
    props = GoogleSlidesProperties(presentation_id=raw)
    assert props.presentation_id == expected
