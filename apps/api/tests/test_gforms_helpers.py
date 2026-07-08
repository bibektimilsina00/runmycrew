"""Unit tests for Google Forms action node helpers."""

from __future__ import annotations

import pytest

from apps.api.app.node_system.nodes.google.gforms.gforms_node import (
    GoogleFormsProperties,
    _build_question_id_to_title,
    _extract_answer_value,
    _normalise_response,
)

# ── _extract_answer_value ──────────────────────────────────────────────


def test_extract_text_single_value():
    answer = {"textAnswers": {"answers": [{"value": "Alice"}]}}
    assert _extract_answer_value(answer) == "Alice"


def test_extract_text_multi_value_returns_list():
    answer = {"textAnswers": {"answers": [{"value": "A"}, {"value": "B"}, {"value": "C"}]}}
    assert _extract_answer_value(answer) == ["A", "B", "C"]


def test_extract_file_upload_returns_metadata_list():
    answer = {
        "fileUploadAnswers": {
            "answers": [
                {"fileId": "f1", "fileName": "doc.pdf", "mimeType": "application/pdf"},
            ]
        }
    }
    assert _extract_answer_value(answer) == [
        {"id": "f1", "name": "doc.pdf", "mime_type": "application/pdf"}
    ]


def test_extract_grade_passes_through():
    answer = {"grade": {"score": 8, "correct": True}}
    assert _extract_answer_value(answer) == {"score": 8, "correct": True}


def test_extract_empty_answer_returns_none():
    assert _extract_answer_value({}) is None
    assert _extract_answer_value({"textAnswers": {"answers": []}}) is None


# ── _build_question_id_to_title ────────────────────────────────────────


def test_build_question_id_to_title_simple():
    form = {
        "items": [
            {
                "title": "What's your name?",
                "questionItem": {"question": {"questionId": "q1"}},
            },
            {
                "title": "Favourite colour?",
                "questionItem": {"question": {"questionId": "q2"}},
            },
        ]
    }
    assert _build_question_id_to_title(form) == {
        "q1": "What's your name?",
        "q2": "Favourite colour?",
    }


def test_build_question_id_to_title_skips_items_without_question():
    """Section breaks and image/text items don't carry a questionId —
    they should be skipped silently."""
    form = {
        "items": [
            {"title": "Section A", "pageBreakItem": {}},
            {"title": "Hello", "textItem": {}},
            {
                "title": "Real question",
                "questionItem": {"question": {"questionId": "qX"}},
            },
        ]
    }
    assert _build_question_id_to_title(form) == {"qX": "Real question"}


def test_build_question_id_to_title_handles_empty_form():
    assert _build_question_id_to_title({}) == {}
    assert _build_question_id_to_title({"items": []}) == {}


# ── _normalise_response ────────────────────────────────────────────────


def test_normalise_response_maps_answers_by_title():
    titles = {"q1": "Name", "q2": "Colour"}
    response = {
        "responseId": "r1",
        "formId": "FORM",
        "lastSubmittedTime": "2026-06-16T12:00:00Z",
        "respondentEmail": "a@b.com",
        "answers": {
            "q1": {"textAnswers": {"answers": [{"value": "Alice"}]}},
            "q2": {"textAnswers": {"answers": [{"value": "Red"}]}},
        },
    }
    normalised = _normalise_response(response, titles)
    assert normalised["response_id"] == "r1"
    assert normalised["form_id"] == "FORM"
    assert normalised["submitted_at"] == "2026-06-16T12:00:00Z"
    assert normalised["respondent_email"] == "a@b.com"
    assert normalised["answers"] == {"Name": "Alice", "Colour": "Red"}


def test_normalise_response_falls_back_to_id_when_title_missing():
    """A response can carry a questionId we haven't seen in the form
    (rare — e.g. between deletes and the next form fetch). We should
    surface the answer under the id so it isn't silently dropped."""
    response = {
        "responseId": "r1",
        "formId": "FORM",
        "answers": {
            "unknownQ": {"textAnswers": {"answers": [{"value": "stray"}]}},
        },
    }
    normalised = _normalise_response(response, titles={})
    assert normalised["answers"] == {"unknownQ": "stray"}


def test_normalise_response_uses_create_time_when_last_submitted_missing():
    response = {
        "responseId": "r1",
        "createTime": "2026-06-16T11:00:00Z",
        "answers": {},
    }
    assert _normalise_response(response, {})["submitted_at"] == "2026-06-16T11:00:00Z"


# ── form_id coercion ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"id": "FORM1", "name": "My Form"}, "FORM1"),
        ("plain", "plain"),
        (None, None),
        ("", None),
        ({"id": ""}, None),
        ({}, None),
    ],
)
def test_form_id_coercion(raw, expected):
    props = GoogleFormsProperties(form_id=raw)
    assert props.form_id == expected
