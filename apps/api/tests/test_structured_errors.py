"""Unit tests for the generic structured-error helper.

These tests pin the wire format so the frontend decoder stays compatible
without coordination — any change to the JSON shape needs to bump
``STRUCTURED_ERROR_SENTINEL`` first.
"""

from __future__ import annotations

import json

from apps.api.app.node_system.base.errors import (
    STRUCTURED_ERROR_SENTINEL,
    make_structured_error,
)


def _decode(error_string: str) -> dict:
    assert error_string.startswith(STRUCTURED_ERROR_SENTINEL)
    return json.loads(error_string[len(STRUCTURED_ERROR_SENTINEL) :])


def test_make_structured_error_minimum_payload():
    raw = make_structured_error("Something failed")
    payload = _decode(raw)
    assert payload["title"] == "Something failed"
    assert payload["summary"] == ""
    assert payload["actions"] == []
    assert payload["raw"] == ""
    assert payload["severity"] == "error"


def test_make_structured_error_full_payload():
    raw = make_structured_error(
        "X broke",
        summary="Y is misconfigured.",
        actions=["Open Y settings.", "Toggle Z."],
        raw="<raw body>",
    )
    payload = _decode(raw)
    assert payload["title"] == "X broke"
    assert payload["summary"] == "Y is misconfigured."
    assert payload["actions"] == ["Open Y settings.", "Toggle Z."]
    assert payload["raw"] == "<raw body>"
    assert payload["severity"] == "error"


def test_make_structured_error_warning_severity():
    raw = make_structured_error("Heads up", severity="warning")
    payload = _decode(raw)
    assert payload["severity"] == "warning"


def test_make_structured_error_preserves_unicode():
    raw = make_structured_error(
        "Échec du nœud",
        summary="说明",
        actions=["重试 ⚙️"],
    )
    # Sentinel + JSON tail must be UTF-8-safe (ensure_ascii=False in
    # the helper) so non-Latin titles / actions don't render as
    # \uXXXX escapes in the inspector card.
    payload = _decode(raw)
    assert payload["title"] == "Échec du nœud"
    assert payload["summary"] == "说明"
    assert payload["actions"] == ["重试 ⚙️"]


def test_make_structured_error_actions_default_empty_list():
    # Make sure callers passing nothing don't get a None — the
    # frontend expects an array even when empty.
    raw = make_structured_error("X", actions=None)
    payload = _decode(raw)
    assert payload["actions"] == []


def test_sentinel_value_is_stable():
    # Bumping this sentinel is a breaking change to the frontend
    # decoder. Pin it here so we can't silently break shipped clients.
    assert STRUCTURED_ERROR_SENTINEL == "__fuse_err_v1__"
