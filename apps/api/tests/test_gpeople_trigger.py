"""Unit tests for the Google Contacts trigger diff logic.

The node was ported to the polling scaffold in PR 0.2; behavior is
identical but the diff functions moved to module-level helpers. Tests
exercise them directly so the trigger's per-poll math stays nailed
down.
"""

from __future__ import annotations

from types import SimpleNamespace

from apps.api.app.node_system.nodes.google.gpeople.trigger_manifest import (
    _diff_contact_updated,
)
from apps.api.app.node_system.scaffolds import diff_known_ids

EVENT_ADDED = "contact_added"
EVENT_UPDATED = "contact_updated"


def _props(max_per_poll: int = 25) -> SimpleNamespace:
    return SimpleNamespace(max_per_poll=max_per_poll)


def _person(rn: str, *, etag: str = "etag0") -> dict:
    return {
        "resourceName": rn,
        "etag": etag,
        "names": [{"displayName": rn}],
    }


# ── contact_added (builtin known_ids strategy) ──────────────────────


def test_added_first_poll_snapshots():
    matches, cursor = diff_known_ids(
        [_person("people/c1"), _person("people/c2")],
        cursor=None,
        id_field="resourceName",
        flatten_fn=None,
        event_id=EVENT_ADDED,
        props=_props(),
    )
    assert matches == []
    assert cursor["event_type"] == EVENT_ADDED
    assert set(cursor["known_ids"]) == {"people/c1", "people/c2"}


def test_added_emits_only_new():
    matches, cursor = diff_known_ids(
        [
            _person("people/c1"),
            _person("people/c2"),
            _person("people/c3"),
        ],
        cursor={"event_type": EVENT_ADDED, "known_ids": ["people/c1"]},
        id_field="resourceName",
        flatten_fn=None,
        event_id=EVENT_ADDED,
        props=_props(),
    )
    assert {m["resourceName"] for m in matches} == {"people/c2", "people/c3"}
    assert set(cursor["known_ids"]) == {"people/c1", "people/c2", "people/c3"}


def test_added_caps_fanout_but_records_overflow():
    matches, cursor = diff_known_ids(
        [_person(f"people/c{i}") for i in range(1, 6)],
        cursor={"event_type": EVENT_ADDED, "known_ids": []},
        id_field="resourceName",
        flatten_fn=None,
        event_id=EVENT_ADDED,
        props=_props(max_per_poll=2),
    )
    assert len(matches) == 2
    # Every resource_name lands in known_ids — overflow records silently
    # so a later poll doesn't fire on the same items.
    assert set(cursor["known_ids"]) == {f"people/c{i}" for i in range(1, 6)}


# ── contact_updated (custom etag-map diff) ──────────────────────────


def test_updated_first_poll_snapshots_etags():
    matches, cursor = _diff_contact_updated(
        [
            _person("people/c1", etag="A"),
            _person("people/c2", etag="B"),
        ],
        cursor=None,
        props=_props(),
        event_id=EVENT_UPDATED,
    )
    assert matches == []
    assert cursor == {
        "event_type": EVENT_UPDATED,
        "etags": {"people/c1": "A", "people/c2": "B"},
    }


def test_updated_emits_on_etag_change():
    matches, cursor = _diff_contact_updated(
        [
            _person("people/c1", etag="A2"),  # changed
            _person("people/c2", etag="B"),  # unchanged
        ],
        cursor={
            "event_type": EVENT_UPDATED,
            "etags": {"people/c1": "A", "people/c2": "B"},
        },
        props=_props(),
        event_id=EVENT_UPDATED,
    )
    assert {m["resource_name"] for m in matches} == {"people/c1"}
    assert cursor["etags"]["people/c1"] == "A2"
    assert cursor["etags"]["people/c2"] == "B"


def test_updated_skips_new_contacts_but_records_silently():
    """Brand-new contacts belong to contact_added, not here. We
    silently record their etag so a later in-place change fires."""
    matches, cursor = _diff_contact_updated(
        [
            _person("people/c1", etag="A"),
            _person("people/c_new", etag="N"),
        ],
        cursor={"event_type": EVENT_UPDATED, "etags": {"people/c1": "A"}},
        props=_props(),
        event_id=EVENT_UPDATED,
    )
    assert matches == []
    assert cursor["etags"]["people/c_new"] == "N"


def test_updated_caps_fanout_and_defers():
    prior = {f"people/c{i}": "old" for i in range(1, 6)}
    new_contacts = [_person(f"people/c{i}", etag="new") for i in range(1, 6)]
    matches, cursor = _diff_contact_updated(
        new_contacts,
        cursor={"event_type": EVENT_UPDATED, "etags": prior},
        props=_props(max_per_poll=2),
        event_id=EVENT_UPDATED,
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
