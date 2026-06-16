"""Unit tests for the Google Tasks trigger diff logic.

Pure-function coverage of `_diff_task_added` + `_diff_task_completed`
under first-poll snapshot, new ids, fan-out cap, status transitions,
and event-type swaps.
"""

from __future__ import annotations

import pytest

from apps.api.app.node_system.nodes.gtasks.gtasks_trigger import (
    EVENT_TASK_ADDED,
    EVENT_TASK_COMPLETED,
    GoogleTasksTriggerNode,
    GoogleTasksTriggerProperties,
)


def _make_node(**overrides) -> GoogleTasksTriggerNode:
    node = GoogleTasksTriggerNode.__new__(GoogleTasksTriggerNode)
    base = {
        "credential": None,
        "event_type": EVENT_TASK_ADDED,
        "tasklist_id": "TL",
        "max_per_poll": 25,
        "poll_interval_seconds": 60,
    }
    base.update(overrides)
    node.props = GoogleTasksTriggerProperties(**base)
    return node


def _task(tid: str, *, completed: bool = False, title: str = "") -> dict:
    return {
        "id": tid,
        "title": title or f"task-{tid}",
        "status": "completed" if completed else "needsAction",
    }


# ── task_added ─────────────────────────────────────────────────────────


def test_task_added_first_poll_snapshots_no_emit():
    node = _make_node()
    matches, cursor = node._diff_task_added(
        tasks=[_task("a"), _task("b")],
        cursor=None,
        tlid="TL",
    )
    assert matches == []
    assert cursor == {"event_type": EVENT_TASK_ADDED, "known_ids": ["a", "b"]}


def test_task_added_emits_only_new_ids():
    node = _make_node()
    matches, cursor = node._diff_task_added(
        tasks=[_task("a"), _task("b"), _task("c")],
        cursor={"event_type": EVENT_TASK_ADDED, "known_ids": ["a"]},
        tlid="TL",
    )
    assert {m["id"] for m in matches} == {"b", "c"}
    assert set(cursor["known_ids"]) == {"a", "b", "c"}


def test_task_added_caps_fanout_and_defers_remainder():
    node = _make_node(max_per_poll=2)
    matches, cursor = node._diff_task_added(
        tasks=[_task(c) for c in ("a", "b", "c", "d", "e")],
        cursor={"event_type": EVENT_TASK_ADDED, "known_ids": ["a"]},
        tlid="TL",
    )
    emitted = {m["id"] for m in matches}
    assert len(emitted) == 2
    # Emitted ids are now known; deferred ids stay out so the next tick
    # picks them up.
    assert emitted.issubset(set(cursor["known_ids"]))
    deferred = {c for c in ("b", "c", "d", "e")} - emitted
    assert deferred.isdisjoint(set(cursor["known_ids"]))


def test_task_added_returns_known_unchanged_when_no_new():
    node = _make_node()
    matches, cursor = node._diff_task_added(
        tasks=[_task("a"), _task("b")],
        cursor={"event_type": EVENT_TASK_ADDED, "known_ids": ["a", "b", "c"]},
        tlid="TL",
    )
    assert matches == []
    # Pre-existing ids that no longer show up are intentionally kept —
    # `known_ids` is monotonically growing, so a deleted task doesn't
    # re-fire if it later comes back with the same id.
    assert "c" in set(cursor["known_ids"])


# ── task_completed ─────────────────────────────────────────────────────


def test_task_completed_first_poll_snapshots_no_emit():
    node = _make_node(event_type=EVENT_TASK_COMPLETED)
    matches, cursor = node._diff_task_completed(
        tasks=[_task("a"), _task("b", completed=True)],
        cursor=None,
        tlid="TL",
    )
    assert matches == []
    assert cursor["event_type"] == EVENT_TASK_COMPLETED
    assert cursor["completion"] == {"a": False, "b": True}


def test_task_completed_emits_on_transition():
    node = _make_node(event_type=EVENT_TASK_COMPLETED)
    matches, cursor = node._diff_task_completed(
        tasks=[_task("a", completed=True), _task("b")],
        cursor={
            "event_type": EVENT_TASK_COMPLETED,
            "completion": {"a": False, "b": False},
        },
        tlid="TL",
    )
    assert {m["id"] for m in matches} == {"a"}
    assert cursor["completion"]["a"] is True
    # Un-transitioned task keeps its prior state.
    assert cursor["completion"]["b"] is False


def test_task_completed_skips_existing_completed():
    """Tasks that were already completed at first poll should NOT
    re-emit when we see them again."""
    node = _make_node(event_type=EVENT_TASK_COMPLETED)
    matches, cursor = node._diff_task_completed(
        tasks=[_task("a", completed=True)],
        cursor={"event_type": EVENT_TASK_COMPLETED, "completion": {"a": True}},
        tlid="TL",
    )
    assert matches == []
    assert cursor["completion"]["a"] is True


def test_task_completed_records_newly_seen_open_tasks_silently():
    """A task that wasn't in the cursor but shows up open should be
    recorded (so a *later* transition to completed fires) but not emit
    on this tick."""
    node = _make_node(event_type=EVENT_TASK_COMPLETED)
    matches, cursor = node._diff_task_completed(
        tasks=[_task("a"), _task("b")],
        cursor={"event_type": EVENT_TASK_COMPLETED, "completion": {"a": False}},
        tlid="TL",
    )
    assert matches == []
    assert cursor["completion"] == {"a": False, "b": False}


def test_task_completed_caps_fanout():
    node = _make_node(event_type=EVENT_TASK_COMPLETED, max_per_poll=2)
    tasks = [_task(c, completed=True) for c in ("a", "b", "c", "d")]
    matches, _ = node._diff_task_completed(
        tasks=tasks,
        cursor={
            "event_type": EVENT_TASK_COMPLETED,
            "completion": {"a": False, "b": False, "c": False, "d": False},
        },
        tlid="TL",
    )
    assert len(matches) == 2


# ── validators ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"id": "TL1", "title": "Personal"}, "TL1"),
        ("plain", "plain"),
        (None, ""),
        ("", ""),
    ],
)
def test_tasklist_id_coercion(raw, expected):
    props = GoogleTasksTriggerProperties(tasklist_id=raw)
    assert props.tasklist_id == expected


def test_event_type_falls_back_to_added_on_bogus():
    props = GoogleTasksTriggerProperties(event_type="bogus")
    assert props.event_type == EVENT_TASK_ADDED
