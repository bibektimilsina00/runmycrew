"""Tests for the Meta subscription sync layer.

The sync layer reconciles `MetaSubscription` rows against the workflow
graph on every save. The DB write path is covered by integration tests
(via FastAPI's test client + a real workflow update); this file guards
the pure logic that drives it — graph scanning + spec/map consistency.

Post-consolidation: trigger nodes are now per-surface (one per
Instagram / Facebook / WhatsApp / Lead Ads) and carry an `event_type`
property that picks the concrete Meta field. The scan layer resolves
`(object, field)` via `_EVENT_TO_FIELD[node_type][event_type]`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apps.api.app.features.meta.service import (
    _EVENT_TO_FIELD,
    _TRIGGER_MAP,
    _TRIGGER_SPECS,
    _scan_meta_triggers,
)


@dataclass
class _FakeWorkflow:
    """Just enough surface to satisfy `_scan_meta_triggers` without
    pulling in SQLModel session machinery."""

    graph: dict[str, Any] = field(default_factory=dict)


def _node(node_id: str, node_type: str, **props: Any) -> dict[str, Any]:
    return {
        "id": node_id,
        "type": node_type,
        "data": {"properties": props},
    }


# ── _EVENT_TO_FIELD ↔ _TRIGGER_MAP consistency ────────────────────────────


def test_every_event_mapping_matches_routing_table() -> None:
    """Drift between the event→field map and the (object, field)→trigger
    routing table would silently drop subscriptions for the affected
    event. The runtime check at import asserts this; the explicit test
    gives a friendlier failure."""
    for trigger_type, event_map in _EVENT_TO_FIELD.items():
        for event_type, (object_type, fb_field) in event_map.items():
            assert _TRIGGER_MAP.get((object_type, fb_field)) == (trigger_type, event_type), (
                trigger_type,
                event_type,
                object_type,
                fb_field,
            )


def test_every_trigger_spec_has_event_mapping() -> None:
    """Every consolidated trigger spec must have at least one event in
    `_EVENT_TO_FIELD`, otherwise its event_type dropdown is empty and
    no slot can ever match."""
    for trigger_type in _TRIGGER_SPECS:
        assert _EVENT_TO_FIELD.get(trigger_type), trigger_type


# ── _scan_meta_triggers — graph → row inputs ──────────────────────────────


def test_scan_ignores_non_meta_nodes() -> None:
    wf = _FakeWorkflow(
        graph={
            "nodes": [
                {"id": "1", "type": "trigger.webhook", "data": {"properties": {}}},
                {"id": "2", "type": "action.http", "data": {"properties": {}}},
            ]
        }
    )
    assert _scan_meta_triggers(wf) == []


def test_scan_picks_up_ig_comment_with_target_and_credential() -> None:
    wf = _FakeWorkflow(
        graph={
            "nodes": [
                _node(
                    "n1",
                    "trigger.meta.instagram",
                    event_type="comment",
                    credential="cred-1",
                    ig_account_id="ig-123",
                ),
            ]
        }
    )
    out = _scan_meta_triggers(wf)
    assert len(out) == 1
    assert out[0] == {
        "node_id": "n1",
        "trigger_type": "trigger.meta.instagram",
        "object_type": "instagram",
        "field": "comments",
        "target_id": "ig-123",
        "credential_id": "cred-1",
    }


def test_scan_strips_blank_target_and_credential() -> None:
    """In-progress nodes (no target id picked yet) should still scan —
    target_id / credential_id come through as empty strings so the
    caller can log skipped rows."""
    wf = _FakeWorkflow(
        graph={
            "nodes": [
                _node(
                    "n1",
                    "trigger.meta.instagram",
                    event_type="comment",
                    credential="",
                    ig_account_id="",
                ),
            ]
        }
    )
    rows = _scan_meta_triggers(wf)
    assert len(rows) == 1
    assert rows[0]["target_id"] == ""
    assert rows[0]["credential_id"] == ""


def test_scan_skips_nodes_without_event_type() -> None:
    """Consolidated triggers require `event_type` to resolve the field.
    A node without it is in-progress UI state — scan must skip it so
    no half-configured MetaSubscription row gets written."""
    wf = _FakeWorkflow(
        graph={
            "nodes": [
                _node("n1", "trigger.meta.instagram", credential="c", ig_account_id="t"),
            ]
        }
    )
    assert _scan_meta_triggers(wf) == []


def test_scan_skips_nodes_with_unknown_event_type() -> None:
    """A typo / stale event_type value (e.g. mid-rename) must skip
    rather than map onto a wrong field."""
    wf = _FakeWorkflow(
        graph={
            "nodes": [
                _node(
                    "n1",
                    "trigger.meta.instagram",
                    event_type="not_a_real_event",
                    credential="c",
                    ig_account_id="t",
                ),
            ]
        }
    )
    assert _scan_meta_triggers(wf) == []


def test_scan_covers_every_trigger_object_pairing() -> None:
    """Each event under each trigger spec must produce a row when
    present in the graph. Catches the case where a new event_type is
    added but its routing entry is forgotten."""
    nodes: list[dict[str, Any]] = []
    expected_pairs: set[tuple[str, str]] = set()
    for trigger_type, event_map in _EVENT_TO_FIELD.items():
        spec = _TRIGGER_SPECS[trigger_type]
        for i, event_type in enumerate(event_map):
            node_id = f"{trigger_type}-{event_type}-{i}"
            nodes.append(
                _node(
                    node_id,
                    trigger_type,
                    event_type=event_type,
                    credential=f"cred-{node_id}",
                    **{spec["target_prop"]: f"target-{node_id}"},
                )
            )
            expected_pairs.add((trigger_type, event_type))
    wf = _FakeWorkflow(graph={"nodes": nodes})
    rows = _scan_meta_triggers(wf)
    assert len(rows) == sum(len(m) for m in _EVENT_TO_FIELD.values())
    # Every (trigger_type, field) pair we emitted is observable in the rows.
    emitted_fields = {(r["trigger_type"], r["field"]) for r in rows}
    expected_fields = {(t, _EVENT_TO_FIELD[t][e][1]) for t, e in expected_pairs}
    assert emitted_fields == expected_fields


def test_scan_handles_missing_data_properties_safely() -> None:
    """A trigger node without `data.properties` (malformed save) must
    not raise. Without `event_type` it's simply skipped, matching the
    in-progress-node behaviour."""
    wf = _FakeWorkflow(graph={"nodes": [{"id": "n1", "type": "trigger.meta.instagram"}]})
    assert _scan_meta_triggers(wf) == []


def test_scan_handles_empty_graph() -> None:
    assert _scan_meta_triggers(_FakeWorkflow()) == []
    assert _scan_meta_triggers(_FakeWorkflow(graph={"nodes": []})) == []
    assert _scan_meta_triggers(_FakeWorkflow(graph={})) == []
