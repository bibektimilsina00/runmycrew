"""Unit tests for the Google Forms trigger.

We can't easily test `poll()` end-to-end without mocking the network,
so these focus on the bits that are pure logic: validator coercion +
the helpers driving the cursor.
"""

from __future__ import annotations

import pytest

from apps.api.app.node_system.nodes.gforms.gforms_trigger import (
    GoogleFormsTriggerProperties,
    _newest_timestamp,
)


@pytest.mark.parametrize(
    ("responses", "expected"),
    [
        ([], None),
        ([{"lastSubmittedTime": "2026-01-01T00:00:00Z"}], "2026-01-01T00:00:00Z"),
        # lastSubmittedTime is preferred over createTime when present.
        (
            [{"lastSubmittedTime": "B", "createTime": "A"}],
            "B",
        ),
        # Falls back to createTime when lastSubmittedTime is absent.
        ([{"createTime": "X"}], "X"),
        # Picks the lexicographically (== chronologically for RFC3339) latest.
        (
            [
                {"lastSubmittedTime": "2026-01-01T00:00:00Z"},
                {"lastSubmittedTime": "2026-02-01T00:00:00Z"},
                {"lastSubmittedTime": "2025-12-01T00:00:00Z"},
            ],
            "2026-02-01T00:00:00Z",
        ),
    ],
)
def test_newest_timestamp(responses, expected):
    assert _newest_timestamp(responses) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"id": "FORM", "name": "My Form"}, "FORM"),
        ("plain", "plain"),
        (None, ""),
        ("", ""),
    ],
)
def test_form_id_coercion(raw, expected):
    props = GoogleFormsTriggerProperties(form_id=raw)
    assert props.form_id == expected
