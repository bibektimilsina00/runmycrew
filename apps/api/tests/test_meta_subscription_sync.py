"""Tests for the Meta subscription sync layer.

The sync layer reconciles `MetaSubscription` rows against the workflow
graph on every save. The DB write path is covered by integration tests
(via FastAPI's test client + a real workflow update); this file guards
the pure logic that drives it — graph scanning + spec/map consistency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apps.api.app.features.meta.service import (
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


# ── _TRIGGER_SPECS ↔ _TRIGGER_MAP consistency ─────────────────────────────


def test_every_trigger_spec_matches_routing_table() -> None:
    """Drift between the two maps would silently drop subscriptions for
    the affected trigger type. The runtime check at import asserts this,
    but the explicit test gives a friendlier failure."""
    for trigger_type, spec in _TRIGGER_SPECS.items():
        key = (spec["object_type"], spec["field"])
        assert _TRIGGER_MAP.get(key) == trigger_type, (trigger_type, spec)


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
                    "trigger.meta.ig_comment",
                    credential="cred-1",
                    ig_account_id="ig-123",
                ),
            ]
        }
    )
    out = _scan_meta_triggers(wf)
    assert len(out) == 1
    row = out[0]
    assert row == {
        "node_id": "n1",
        "trigger_type": "trigger.meta.ig_comment",
        "object_type": "instagram",
        "field": "comments",
        "target_id": "ig-123",
        "credential_id": "cred-1",
    }


def test_scan_strips_blank_target_and_credential() -> None:
    """In-progress nodes (no target id picked yet) should scan but the
    caller skips them at write time. The scan layer surfaces them as
    empty-string fields so the caller can log."""
    wf = _FakeWorkflow(
        graph={
            "nodes": [
                _node("n1", "trigger.meta.ig_comment", credential="", ig_account_id=""),
            ]
        }
    )
    rows = _scan_meta_triggers(wf)
    assert len(rows) == 1
    assert rows[0]["target_id"] == ""
    assert rows[0]["credential_id"] == ""


def test_scan_covers_every_trigger_object_pairing() -> None:
    """Each trigger spec must produce a row when present in the graph.
    Catches the case where a new trigger node is added but its routing
    spec is forgotten."""
    nodes = []
    for i, (trigger_type, spec) in enumerate(_TRIGGER_SPECS.items()):
        nodes.append(
            _node(
                f"n{i}",
                trigger_type,
                credential=f"cred-{i}",
                **{spec["target_prop"]: f"target-{i}"},
            )
        )
    wf = _FakeWorkflow(graph={"nodes": nodes})
    rows = _scan_meta_triggers(wf)
    assert len(rows) == len(_TRIGGER_SPECS)
    trigger_types_emitted = {r["trigger_type"] for r in rows}
    assert trigger_types_emitted == set(_TRIGGER_SPECS.keys())


def test_scan_handles_missing_data_properties_safely() -> None:
    """A trigger node without `data.properties` (malformed save) must
    surface as a row with empty fields — never raise."""
    wf = _FakeWorkflow(graph={"nodes": [{"id": "n1", "type": "trigger.meta.ig_comment"}]})
    rows = _scan_meta_triggers(wf)
    assert rows == [
        {
            "node_id": "n1",
            "trigger_type": "trigger.meta.ig_comment",
            "object_type": "instagram",
            "field": "comments",
            "target_id": "",
            "credential_id": "",
        }
    ]


def test_scan_handles_empty_graph() -> None:
    assert _scan_meta_triggers(_FakeWorkflow()) == []
    assert _scan_meta_triggers(_FakeWorkflow(graph={"nodes": []})) == []
    assert _scan_meta_triggers(_FakeWorkflow(graph={})) == []
