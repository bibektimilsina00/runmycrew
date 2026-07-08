"""Unit tests for Google Docs action node helpers."""

from __future__ import annotations

import pytest

from apps.api.app.node_system.nodes.google.gdocs.gdocs_node import (
    GoogleDocsProperties,
    _color_field,
    _extract_doc_text,
)

# ── _extract_doc_text ───────────────────────────────────────────────────


def test_extract_doc_text_joins_runs():
    doc = {
        "body": {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {"textRun": {"content": "Hello "}},
                            {"textRun": {"content": "world"}},
                        ]
                    }
                },
                {"paragraph": {"elements": [{"textRun": {"content": "\nSecond para."}}]}},
            ]
        }
    }
    assert _extract_doc_text(doc) == "Hello world\nSecond para."


def test_extract_doc_text_skips_non_paragraph_entries():
    """Body content can include tables / section breaks too — they
    don't have a `paragraph` key. Just skip them."""
    doc = {
        "body": {
            "content": [
                {"sectionBreak": {}},
                {"paragraph": {"elements": [{"textRun": {"content": "Only this."}}]}},
                {"table": {}},
            ]
        }
    }
    assert _extract_doc_text(doc) == "Only this."


def test_extract_doc_text_skips_elements_without_textrun():
    """An element can be an inlineObject (image) — no textRun. Drop it."""
    doc = {
        "body": {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {"textRun": {"content": "Before "}},
                            {"inlineObjectElement": {"inlineObjectId": "kix.x"}},
                            {"textRun": {"content": " after"}},
                        ]
                    }
                }
            ]
        }
    }
    assert _extract_doc_text(doc) == "Before  after"


def test_extract_doc_text_handles_missing_body():
    assert _extract_doc_text({}) == ""
    assert _extract_doc_text({"body": {}}) == ""
    assert _extract_doc_text({"body": {"content": []}}) == ""


def test_extract_doc_text_ignores_non_string_content():
    """Defensive — Docs always returns strings, but if the wire data
    somehow has a non-string we shouldn't blow up the workflow."""
    doc = {
        "body": {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {"textRun": {"content": None}},
                            {"textRun": {"content": 42}},
                            {"textRun": {"content": "ok"}},
                        ]
                    }
                }
            ]
        }
    }
    assert _extract_doc_text(doc) == "ok"


# ── _color_field ────────────────────────────────────────────────────────


def test_color_field_well_formed_hex():
    assert _color_field("#336699") == {
        "color": {
            "rgbColor": {
                "red": 0x33 / 255,
                "green": 0x66 / 255,
                "blue": 0x99 / 255,
            }
        }
    }


def test_color_field_accepts_missing_hash():
    assert _color_field("ff0000") == {
        "color": {"rgbColor": {"red": 1.0, "green": 0.0, "blue": 0.0}}
    }


@pytest.mark.parametrize("bad", ["", "abc", "#nothex", "#abc"])
def test_color_field_returns_none_on_invalid(bad):
    assert _color_field(bad) is None


# ── document_id coercion ────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"id": "abc123", "name": "My Doc"}, "abc123"),
        ("xyz", "xyz"),
        (None, None),
        ("", None),
        ({"id": ""}, None),
        ({}, None),
    ],
)
def test_document_id_coercion(raw, expected):
    props = GoogleDocsProperties(document_id=raw)
    assert props.document_id == expected
