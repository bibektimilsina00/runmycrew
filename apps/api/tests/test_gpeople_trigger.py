"""Unit tests for the Google Contacts trigger diff logic."""

from __future__ import annotations

import pytest

from apps.api.app.node_system.nodes.gpeople.gpeople_trigger import (
    EVENT_ADDED,
    EVENT_UPDATED,
    GooglePeopleTriggerNode,
    GooglePeopleTriggerProperties,
)


def _make_node(**overrides) -> GooglePeopleTriggerNode:
    node = GooglePeopleTriggerNode.__new__(GooglePeopleTriggerNode)
    base = {
        "credential": None,
        "event_type": EVENT_ADDED,
        "max_per_poll": 25,
        "poll_interval_seconds": 60,
    }
    base.update(overrides)
    node.props = GooglePeopleTriggerProperties(**base)
    return node


def _person(rn: str, *, etag: str = "etag0") -> dict:
    return {
        "resourceName": rn,
        "etag": etag,
        "names": [{"displayName": rn}],
    }


# ── contact_added ───────────────────────────────────────────────────────


def test_added_first_poll_snapshots():
    node = _make_node()
    matches, cursor = node._diff_added(
        connections=[_person("people/c1"), _person("people/c2")],
        cursor=None,
    )
    assert matches == []
    assert cursor == {
        "event_type": EVENT_ADDED,
        "known_ids": ["people/c1", "people/c2"],
    }


def test_added_emits_only_new():
    node = _make_node()
    matches, cursor = node._diff_added(
        connections=[
            _person("people/c1"),
            _person("people/c2"),
            _person("people/c3"),
        ],
        cursor={"event_type": EVENT_ADDED, "known_ids": ["people/c1"]},
    )
    assert {m["resource_name"] for m in matches} == {"people/c2", "people/c3"}
    assert set(cursor["known_ids"]) == {"people/c1", "people/c2", "people/c3"}


def test_added_caps_fanout():
    node = _make_node(max_per_poll=2)
    matches, cursor = node._diff_added(
        connections=[_person(f"people/c{i}") for i in range(1, 6)],
        cursor={"event_type": EVENT_ADDED, "known_ids": []},
    )
    assert len(matches) == 2
    emitted = {m["resource_name"] for m in matches}
    deferred = {f"people/c{i}" for i in range(1, 6)} - emitted
    assert deferred.isdisjoint(set(cursor["known_ids"]))


# ── contact_updated ────────────────────────────────────────────────────


def test_updated_first_poll_snapshots_etags():
    node = _make_node(event_type=EVENT_UPDATED)
    matches, cursor = node._diff_updated(
        connections=[
            _person("people/c1", etag="A"),
            _person("people/c2", etag="B"),
        ],
        cursor=None,
    )
    assert matches == []
    assert cursor == {
        "event_type": EVENT_UPDATED,
        "etags": {"people/c1": "A", "people/c2": "B"},
    }


def test_updated_emits_on_etag_change():
    node = _make_node(event_type=EVENT_UPDATED)
    matches, cursor = node._diff_updated(
        connections=[
            _person("people/c1", etag="A2"),  # changed
            _person("people/c2", etag="B"),  # unchanged
        ],
        cursor={
            "event_type": EVENT_UPDATED,
            "etags": {"people/c1": "A", "people/c2": "B"},
        },
    )
    assert {m["resource_name"] for m in matches} == {"people/c1"}
    assert cursor["etags"]["people/c1"] == "A2"
    assert cursor["etags"]["people/c2"] == "B"


def test_updated_skips_new_contacts_but_records_silently():
    """Brand-new contacts belong to contact_added, not here. We
    silently record their etag so a later in-place change fires."""
    node = _make_node(event_type=EVENT_UPDATED)
    matches, cursor = node._diff_updated(
        connections=[
            _person("people/c1", etag="A"),
            _person("people/c_new", etag="N"),
        ],
        cursor={"event_type": EVENT_UPDATED, "etags": {"people/c1": "A"}},
    )
    assert matches == []
    assert cursor["etags"]["people/c_new"] == "N"


def test_updated_caps_fanout_and_defers():
    node = _make_node(event_type=EVENT_UPDATED, max_per_poll=2)
    prior = {f"people/c{i}": "old" for i in range(1, 6)}
    new = [_person(f"people/c{i}", etag="new") for i in range(1, 6)]
    matches, cursor = node._diff_updated(
        connections=new,
        cursor={"event_type": EVENT_UPDATED, "etags": prior},
    )
    assert len(matches) == 2
    emitted = {m["resource_name"] for m in matches}
    # Emitted contacts advance to the new etag.
    for rn in emitted:
        assert cursor["etags"][rn] == "new"
    # Deferred ones keep the prior etag so they re-fire next tick.
    deferred = {f"people/c{i}" for i in range(1, 6)} - emitted
    for rn in deferred:
        assert cursor["etags"][rn] == "old"


# ── validators ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (EVENT_ADDED, EVENT_ADDED),
        (EVENT_UPDATED, EVENT_UPDATED),
        ("bogus", EVENT_ADDED),
        ("", EVENT_ADDED),
        (None, EVENT_ADDED),
    ],
)
def test_event_type_coercion(raw, expected):
    props = GooglePeopleTriggerProperties(event_type=raw)
    assert props.event_type == expected
