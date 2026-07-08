"""Unit tests for Google Slides action node helpers."""

from __future__ import annotations

import pytest

from apps.api.app.node_system.nodes.google.gslides.gslides_node import (
    GoogleSlidesProperties,
    _build_outline_slide_requests,
    _coerce_outline_string,
    _collect_speaker_notes_inputs,
    _element_kind,
    _extract_element_text,
    _extract_slide_text,
    _find_text_placeholder,
    _gen_object_id,
    _opaque_color_field,
    _optional_color_field,
    _placement,
    _slide_insertion_index,
    _text_range,
    _validate_outline,
)

# ── _opaque_color_field ────────────────────────────────────────────────
#
# Raw OpaqueColor — what SolidFill.color (page background, shape fill)
# expects. No `opaqueColor` wrapper.


def test_opaque_color_field_well_formed_hex():
    assert _opaque_color_field("#336699") == {
        "rgbColor": {
            "red": 0x33 / 255,
            "green": 0x66 / 255,
            "blue": 0x99 / 255,
        }
    }


def test_opaque_color_field_accepts_missing_hash():
    assert _opaque_color_field("ff0000") == {"rgbColor": {"red": 1.0, "green": 0.0, "blue": 0.0}}


@pytest.mark.parametrize("bad", ["", "abc", "#nothex", "#abc"])
def test_opaque_color_field_returns_none_on_invalid(bad):
    assert _opaque_color_field(bad) is None


# ── _optional_color_field ──────────────────────────────────────────────
#
# OptionalColor wrapper — what TextStyle.foregroundColor /
# TextStyle.backgroundColor expect.


def test_optional_color_field_well_formed_hex():
    assert _optional_color_field("#336699") == {
        "opaqueColor": {
            "rgbColor": {
                "red": 0x33 / 255,
                "green": 0x66 / 255,
                "blue": 0x99 / 255,
            }
        }
    }


@pytest.mark.parametrize("bad", ["", "abc", "#nothex", "#abc"])
def test_optional_color_field_returns_none_on_invalid(bad):
    assert _optional_color_field(bad) is None


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


# ── _find_text_placeholder ─────────────────────────────────────────────


def _placeholder_element(object_id: str, ptype: str) -> dict:
    return {
        "objectId": object_id,
        "shape": {"placeholder": {"type": ptype}},
    }


def test_find_text_placeholder_returns_subtitle_when_preferred_first():
    slide = {
        "pageElements": [
            _placeholder_element("title_obj", "CENTERED_TITLE"),
            _placeholder_element("subtitle_obj", "SUBTITLE"),
        ]
    }
    assert (
        _find_text_placeholder(slide, preferred=("SUBTITLE", "BODY", "CENTERED_TITLE", "TITLE"))
        == "subtitle_obj"
    )


def test_find_text_placeholder_falls_back_to_title_when_no_subtitle():
    slide = {"pageElements": [_placeholder_element("title_obj", "CENTERED_TITLE")]}
    assert (
        _find_text_placeholder(slide, preferred=("SUBTITLE", "BODY", "CENTERED_TITLE", "TITLE"))
        == "title_obj"
    )


def test_find_text_placeholder_returns_none_on_blank_slide():
    """A BLANK layout has no placeholders — the caller should skip the
    seed step silently."""
    slide = {"pageElements": [{"objectId": "non_placeholder_shape", "shape": {}}]}
    assert (
        _find_text_placeholder(slide, preferred=("SUBTITLE", "BODY", "CENTERED_TITLE", "TITLE"))
        is None
    )


def test_find_text_placeholder_ignores_unrelated_placeholders():
    slide = {
        "pageElements": [
            _placeholder_element("img_ph", "PICTURE"),
            _placeholder_element("chart_ph", "OBJECT"),
        ]
    }
    assert (
        _find_text_placeholder(slide, preferred=("SUBTITLE", "BODY", "CENTERED_TITLE", "TITLE"))
        is None
    )


# ── outline builder ───────────────────────────────────────────────────


def _types_of_mappings(create_request):
    return [
        m["layoutPlaceholder"]["type"]
        for m in create_request["createSlide"].get("placeholderIdMappings") or []
    ]


def test_outline_title_layout_maps_centered_title_and_subtitle():
    spec = {"layout": "TITLE", "title": "Q1 review", "subtitle": "March 2026"}
    requests, sid, ph = _build_outline_slide_requests(spec, insertion_index=0)
    assert _types_of_mappings(requests[0]) == ["CENTERED_TITLE", "SUBTITLE"]
    assert ph["title"] and ph["body"]
    # The insertText requests use the same objectIds we assigned via
    # placeholderIdMappings so there's no follow-up fetch needed.
    insert_targets = [r["insertText"]["objectId"] for r in requests if "insertText" in r]
    assert set(insert_targets) == {ph["title"], ph["body"]}


def test_outline_title_and_body_layout_maps_title_and_body():
    spec = {"layout": "TITLE_AND_BODY", "title": "Highlights", "body": "x\ny"}
    requests, _, ph = _build_outline_slide_requests(spec, insertion_index=2)
    assert _types_of_mappings(requests[0]) == ["TITLE", "BODY"]
    assert requests[0]["createSlide"]["insertionIndex"] == 2
    insert_targets = [r["insertText"]["objectId"] for r in requests if "insertText" in r]
    assert ph["title"] in insert_targets
    assert ph["body"] in insert_targets


def test_outline_falls_back_to_title_and_body_on_unknown_layout():
    """An LLM might emit a layout name we don't know. We should still
    produce a usable slide instead of erroring."""
    spec = {"layout": "FANCY_NEW_LAYOUT", "title": "x", "body": "y"}
    requests, _, _ = _build_outline_slide_requests(spec, insertion_index=0)
    assert (
        requests[0]["createSlide"]["slideLayoutReference"]["predefinedLayout"] == "TITLE_AND_BODY"
    )


def test_outline_accepts_subtitle_as_body_alias_for_non_title_layouts():
    spec = {"layout": "TITLE_AND_BODY", "title": "x", "subtitle": "from subtitle key"}
    requests, _, ph = _build_outline_slide_requests(spec, insertion_index=0)
    body_inserts = [
        r["insertText"]["text"]
        for r in requests
        if "insertText" in r and r["insertText"]["objectId"] == ph["body"]
    ]
    assert body_inserts == ["from subtitle key"]


def test_outline_accepts_content_as_third_alias():
    spec = {"layout": "TITLE_AND_BODY", "title": "x", "content": "from content key"}
    requests, _, ph = _build_outline_slide_requests(spec, insertion_index=0)
    body_inserts = [
        r["insertText"]["text"]
        for r in requests
        if "insertText" in r and r["insertText"]["objectId"] == ph["body"]
    ]
    assert body_inserts == ["from content key"]


def test_outline_emits_image_request_when_image_url_present():
    spec = {"layout": "BLANK", "image_url": "https://thumb.example/x.png"}
    requests, sid, _ = _build_outline_slide_requests(spec, insertion_index=0)
    images = [r for r in requests if "createImage" in r]
    assert len(images) == 1
    assert images[0]["createImage"]["url"] == "https://thumb.example/x.png"
    assert images[0]["createImage"]["elementProperties"]["pageObjectId"] == sid


def test_outline_emits_background_request_when_color_present():
    spec = {"layout": "BLANK", "background_color": "#1a73e8"}
    requests, sid, _ = _build_outline_slide_requests(spec, insertion_index=0)
    bg = [r for r in requests if "updatePageProperties" in r]
    assert len(bg) == 1
    assert bg[0]["updatePageProperties"]["objectId"] == sid


def test_outline_skips_background_on_invalid_hex():
    """Bad hex shouldn't blow up the whole slide — drop it silently
    and emit a valid slide otherwise."""
    spec = {"layout": "BLANK", "background_color": "not-a-hex"}
    requests, _, _ = _build_outline_slide_requests(spec, insertion_index=0)
    assert not any("updatePageProperties" in r for r in requests)


def test_outline_blank_layout_does_not_emit_text_inserts():
    """BLANK layout has no placeholders. Title/body text should be
    silently dropped instead of throwing — caller can re-issue a
    text_box insert if they need to."""
    spec = {"layout": "BLANK", "title": "ignored", "body": "ignored"}
    requests, _, ph = _build_outline_slide_requests(spec, insertion_index=0)
    assert ph["title"] is None
    assert ph["body"] is None
    assert not any("insertText" in r for r in requests)


def test_collect_speaker_notes_inputs_pairs_specs_with_ids():
    specs = [
        {"title": "a", "notes": "n1"},
        {"title": "b"},
        {"title": "c", "speaker_notes": "n3"},
    ]
    ids = ["s1", "s2", "s3"]
    assert _collect_speaker_notes_inputs(specs, ids) == [("s1", "n1"), ("s3", "n3")]


def test_collect_speaker_notes_handles_short_id_list():
    specs = [{"title": "a", "notes": "n"}]
    assert _collect_speaker_notes_inputs(specs, []) == []


# ── _validate_outline ─────────────────────────────────────────────────


def test_validate_outline_accepts_well_formed_list():
    raw = [{"title": "A"}, {"title": "B"}]
    out = _validate_outline(raw)
    assert out == raw


def test_validate_outline_rejects_empty_list():
    result = _validate_outline([])
    assert not getattr(result, "success", True)


def test_validate_outline_rejects_non_list_inputs():
    for bad in [None, "string", 42, {"slides": []}]:
        result = _validate_outline(bad)
        assert not getattr(result, "success", True)


def test_validate_outline_drops_non_dict_entries():
    """If the LLM mixed in a stray string, drop it and keep the rest."""
    raw = [{"title": "A"}, "garbage", 7, {"title": "B"}]
    out = _validate_outline(raw)
    assert out == [{"title": "A"}, {"title": "B"}]


# ── outline parser (string vs list inputs) ────────────────────────────


def test_outline_accepts_python_list_unchanged():
    props = GoogleSlidesProperties(outline=[{"title": "A"}, {"title": "B"}])
    assert props.outline == [{"title": "A"}, {"title": "B"}]


def test_outline_parses_json_string_into_list():
    """Pasting JSON into the multiline string field still works — we
    parse it before Pydantic sees it."""
    raw = '[{"title": "A"}, {"title": "B"}]'
    props = GoogleSlidesProperties(outline=raw)
    assert props.outline == [{"title": "A"}, {"title": "B"}]


def test_outline_passes_through_unresolved_expression_string():
    """An unresolved `{{ … }}` should round-trip as the raw string —
    `_validate_outline` will surface the error."""
    raw = "{{ $agent.output }}"
    props = GoogleSlidesProperties(outline=raw)
    assert props.outline == raw


def test_outline_returns_none_for_blank_input():
    assert GoogleSlidesProperties(outline=" ").outline is None
    assert GoogleSlidesProperties(outline="").outline is None


def test_outline_passes_dict_through_for_validator_to_reject():
    raw = {"slides": []}
    assert GoogleSlidesProperties(outline=raw).outline == raw


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


# ── _coerce_outline_string (LLM-output edge cases) ────────────────────


def test_coerce_outline_parses_clean_json_array():
    raw = '[{"layout": "TITLE", "title": "x"}]'
    assert _coerce_outline_string(raw) == [{"layout": "TITLE", "title": "x"}]


def test_coerce_outline_strips_markdown_fences():
    raw = '```json\n[{"layout": "TITLE", "title": "x"}]\n```'
    assert _coerce_outline_string(raw) == [{"layout": "TITLE", "title": "x"}]


def test_coerce_outline_strips_bare_code_fences():
    raw = '```\n[{"layout": "TITLE"}]\n```'
    assert _coerce_outline_string(raw) == [{"layout": "TITLE"}]


def test_coerce_outline_handles_prose_wrapper():
    """LLMs love prefixing with 'Here is the JSON:'."""
    raw = 'Here is your outline: [{"layout": "TITLE", "title": "x"}]. Enjoy!'
    assert _coerce_outline_string(raw) == [{"layout": "TITLE", "title": "x"}]


def test_coerce_outline_normalises_smart_quotes():
    """Word / Notion paste mangles `"` into curly quotes."""
    raw = "[{“layout”:“TITLE”,“title”:“x”}]"
    assert _coerce_outline_string(raw) == [{"layout": "TITLE", "title": "x"}]


def test_coerce_outline_tolerates_trailing_commas():
    raw = '[{"layout": "TITLE", "title": "x",}, {"layout": "BLANK",},]'
    assert _coerce_outline_string(raw) == [
        {"layout": "TITLE", "title": "x"},
        {"layout": "BLANK"},
    ]


def test_coerce_outline_returns_none_on_garbage():
    assert _coerce_outline_string("nope nothing valid here") is None


# ── _validate_outline diagnostic errors ───────────────────────────────


def test_validate_outline_string_input_includes_sample():
    result = _validate_outline("not parseable")
    assert not result.success
    assert "First 200 chars" in result.error
    assert "not parseable" in result.error


def test_validate_outline_dict_input_lists_keys():
    """Common LLM mistake: returning `{slides: [...]}` instead of bare array."""
    result = _validate_outline({"slides": [], "meta": {}})
    assert not result.success
    assert "JSON ARRAY" in result.error
    assert "slides" in result.error


def test_validate_outline_passes_through_well_formed_list():
    raw = [{"title": "A"}, {"title": "B"}]
    assert _validate_outline(raw) == raw
