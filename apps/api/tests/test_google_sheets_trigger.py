"""Unit tests for the Google Sheets trigger diff logic.

We don't hit Sheets here — the diff functions are pure given (values,
cursor). One test per branch of each event type.
"""

from __future__ import annotations

import pytest

from apps.api.app.node_system.nodes.google.google_sheets.google_sheets_trigger import (
    EVENT_ROW_ADDED,
    EVENT_ROW_UPDATED,
    GoogleSheetsTriggerNode,
    GoogleSheetsTriggerProperties,
    _hash_row,
)


def _make_node(**overrides: object) -> GoogleSheetsTriggerNode:
    node = GoogleSheetsTriggerNode.__new__(GoogleSheetsTriggerNode)
    base = {
        "credential": None,
        "event_type": EVENT_ROW_ADDED,
        "spreadsheet_id": "SID",
        "sheet_name": "Sheet1",
        "last_column": "Z",
        "max_rows_per_poll": 25,
        "poll_interval_seconds": 60,
    }
    base.update(overrides)
    node.props = GoogleSheetsTriggerProperties(**base)
    return node


# ── row_added ───────────────────────────────────────────────────────────


def test_row_added_first_poll_snapshots_no_emit():
    node = _make_node()
    matches, cursor = node._diff_row_added(
        values=[["h1", "h2"], ["a", "b"]],
        cursor=None,
        sid="SID",
        sheet_name="Sheet1",
        max_rows=25,
    )
    assert matches == []
    assert cursor == {"event_type": EVENT_ROW_ADDED, "last_row_count": 2}


def test_row_added_emits_only_new_rows():
    node = _make_node()
    matches, cursor = node._diff_row_added(
        values=[["h1"], ["a"], ["b"], ["c"]],
        cursor={"event_type": EVENT_ROW_ADDED, "last_row_count": 2},
        sid="SID",
        sheet_name="Sheet1",
        max_rows=25,
    )
    assert [m["row_index"] for m in matches] == [3, 4]
    assert [m["values"] for m in matches] == [["b"], ["c"]]
    assert cursor == {"event_type": EVENT_ROW_ADDED, "last_row_count": 4}
    assert all(m["event_type"] == EVENT_ROW_ADDED for m in matches)


def test_row_added_caps_at_max_rows_per_poll():
    node = _make_node(max_rows_per_poll=2)
    values = [["h1"]] + [[f"row{i}"] for i in range(1, 6)]  # header + 5 rows
    matches, cursor = node._diff_row_added(
        values=values,
        cursor={"event_type": EVENT_ROW_ADDED, "last_row_count": 1},
        sid="SID",
        sheet_name="Sheet1",
        max_rows=2,
    )
    assert len(matches) == 2
    # Cursor advances only past what we emitted — remainder fires next tick.
    assert cursor == {"event_type": EVENT_ROW_ADDED, "last_row_count": 3}


def test_row_added_shrink_silently_rewinds():
    node = _make_node()
    matches, cursor = node._diff_row_added(
        values=[["h1"]],
        cursor={"event_type": EVENT_ROW_ADDED, "last_row_count": 5},
        sid="SID",
        sheet_name="Sheet1",
        max_rows=25,
    )
    assert matches == []
    assert cursor == {"event_type": EVENT_ROW_ADDED, "last_row_count": 1}


# ── row_updated ─────────────────────────────────────────────────────────


def test_row_updated_first_poll_hashes_no_emit():
    node = _make_node(event_type=EVENT_ROW_UPDATED)
    values = [["h1"], ["a"], ["b"]]
    matches, cursor = node._diff_row_updated(
        values=values,
        cursor=None,
        sid="SID",
        sheet_name="Sheet1",
        max_rows=25,
    )
    assert matches == []
    assert cursor["event_type"] == EVENT_ROW_UPDATED
    assert cursor["row_hashes"] == [_hash_row(r) for r in values]


def test_row_updated_emits_only_changed_rows():
    node = _make_node(event_type=EVENT_ROW_UPDATED)
    prior = [["h1"], ["a"], ["b"], ["c"]]
    new = [["h1"], ["a"], ["b_changed"], ["c"]]
    matches, cursor = node._diff_row_updated(
        values=new,
        cursor={
            "event_type": EVENT_ROW_UPDATED,
            "row_hashes": [_hash_row(r) for r in prior],
        },
        sid="SID",
        sheet_name="Sheet1",
        max_rows=25,
    )
    assert [m["row_index"] for m in matches] == [3]
    assert matches[0]["values"] == ["b_changed"]
    assert cursor["row_hashes"] == [_hash_row(r) for r in new]


def test_row_updated_skips_appended_rows():
    """Newly *added* rows aren't `row_updated` events — that's
    `row_added`'s job. Adding shouldn't emit here."""
    node = _make_node(event_type=EVENT_ROW_UPDATED)
    prior = [["h1"], ["a"]]
    new = [["h1"], ["a"], ["b"], ["c"]]
    matches, cursor = node._diff_row_updated(
        values=new,
        cursor={
            "event_type": EVENT_ROW_UPDATED,
            "row_hashes": [_hash_row(r) for r in prior],
        },
        sid="SID",
        sheet_name="Sheet1",
        max_rows=25,
    )
    assert matches == []
    assert cursor["row_hashes"] == [_hash_row(r) for r in new]


def test_row_updated_caps_emits_and_persists_unemitted_diffs():
    node = _make_node(event_type=EVENT_ROW_UPDATED)
    prior = [["h"], ["a"], ["b"], ["c"], ["d"]]
    new = [["h"], ["a2"], ["b2"], ["c2"], ["d2"]]
    matches, cursor = node._diff_row_updated(
        values=new,
        cursor={
            "event_type": EVENT_ROW_UPDATED,
            "row_hashes": [_hash_row(r) for r in prior],
        },
        sid="SID",
        sheet_name="Sheet1",
        max_rows=2,
    )
    assert len(matches) == 2
    assert [m["row_index"] for m in matches] == [2, 3]
    # Emitted rows advance to the new hash; un-emitted rows keep prior
    # hashes so the next tick still sees them as changed.
    persisted = cursor["row_hashes"]
    assert persisted[1] == _hash_row(new[1])  # emitted row 2
    assert persisted[2] == _hash_row(new[2])  # emitted row 3
    assert persisted[3] == _hash_row(prior[3])  # deferred row 4
    assert persisted[4] == _hash_row(prior[4])  # deferred row 5


# ── coercion validators ────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"id": "abc", "name": "Q1 Sheet"}, "abc"),
        ("xyz", "xyz"),
        (None, ""),
        ("", ""),
    ],
)
def test_spreadsheet_id_coercion(raw, expected):
    props = GoogleSheetsTriggerProperties(spreadsheet_id=raw)
    assert props.spreadsheet_id == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"title": "Sales", "sheet_id": 42}, "Sales"),
        ("Sales", "Sales"),
        (None, "Sheet1"),
        ("", "Sheet1"),
    ],
)
def test_sheet_name_coercion(raw, expected):
    props = GoogleSheetsTriggerProperties(sheet_name=raw)
    assert props.sheet_name == expected


def test_event_type_coercion_falls_back_to_row_added_on_bogus_input():
    props = GoogleSheetsTriggerProperties(event_type="not-a-real-event")
    assert props.event_type == EVENT_ROW_ADDED
