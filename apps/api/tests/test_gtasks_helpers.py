"""Unit tests for Google Tasks node helpers."""

from __future__ import annotations

import pytest

from apps.api.app.node_system.nodes.gtasks.gtasks_node import _normalise_due


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # Date-only padded to midnight UTC.
        ("2026-05-15", "2026-05-15T00:00:00Z"),
        ("2024-01-01", "2024-01-01T00:00:00Z"),
        # Full RFC3339 passes through unchanged.
        ("2026-05-15T12:30:00Z", "2026-05-15T12:30:00Z"),
        ("2026-05-15T12:30:00.123Z", "2026-05-15T12:30:00.123Z"),
        ("2026-05-15T12:30:00+05:30", "2026-05-15T12:30:00+05:30"),
        # Anything that doesn't match the date-only shape passes through —
        # let Google's parser surface the error to the user.
        ("garbage", "garbage"),
        ("2026/05/15", "2026/05/15"),
        ("", ""),
    ],
)
def test_normalise_due(raw, expected):
    assert _normalise_due(raw) == expected
