"""Unit tests for the ServiceNow integration (Phase 4.5)."""

from __future__ import annotations

from apps.api.app.node_system.nodes.servicenow.trigger_manifest import (
    _flatten_change,
    _flatten_incident,
    _pull_ref,
)


def test_pull_ref_handles_bare_sys_id() -> None:
    """ServiceNow returns reference fields as either a bare string
    (when sysparm_display_value is missing) or as a `{value, link,
    display_value}` object. Normalize both shapes."""
    assert _pull_ref("abc123") == "abc123"
    assert _pull_ref({"display_value": "Priority 1", "value": "1"}) == "Priority 1"
    assert _pull_ref({"value": "1"}) == "1"
    assert _pull_ref(None) == ""
    assert _pull_ref({}) == ""


def test_incident_flatten_hoists_reference_display_values() -> None:
    """The flatten hoists nested `display_value` fields so downstream
    nodes see human-readable state / priority / assignee rather than
    opaque sys_ids."""
    incident = {
        "sys_id": "abc123",
        "number": "INC0012345",
        "short_description": "Login broken",
        "state": {"display_value": "In Progress", "value": "2"},
        "priority": {"display_value": "1 - Critical", "value": "1"},
        "assignment_group": {"display_value": "Platform", "value": "grp1"},
        "assigned_to": {"display_value": "Alice", "value": "u1"},
        "caller_id": {"display_value": "Bob", "value": "u2"},
        "sys_created_on": "2026-07-04 12:00:00",
        "sys_updated_on": "2026-07-04 12:34:56",
    }
    out = _flatten_incident(incident)
    assert out["number"] == "INC0012345"
    assert out["state"] == "In Progress"
    assert out["priority"] == "1 - Critical"
    assert out["assignment_group"] == "Platform"
    assert out["assigned_to"] == "Alice"


def test_change_flatten_captures_risk_type_and_window() -> None:
    """Change requests carry risk + type + start/end dates that
    incidents don't — flatten must surface those."""
    change = {
        "sys_id": "chg1",
        "number": "CHG0000001",
        "short_description": "Kubernetes upgrade",
        "state": {"display_value": "Assess"},
        "risk": {"display_value": "Moderate"},
        "type": {"display_value": "Normal"},
        "start_date": "2026-07-10 22:00:00",
        "end_date": "2026-07-10 23:00:00",
        "requested_by": {"display_value": "Alice"},
    }
    out = _flatten_change(change)
    assert out["risk"] == "Moderate"
    assert out["type"] == "Normal"
    assert out["start_date"] == "2026-07-10 22:00:00"
    assert out["requested_by"] == "Alice"


def test_servicenow_manifest_registers_all_ops() -> None:
    from apps.api.app.node_system.nodes.servicenow.manifest import MANIFEST

    op_ids = {o.id for o in MANIFEST.operations}
    assert {
        "get_record",
        "list_records",
        "create_record",
        "update_record",
        "delete_record",
        "create_incident",
        "update_incident",
        "get_incident",
        "list_incidents",
        "create_change_request",
    } <= op_ids


def test_servicenow_trigger_covers_all_four_sim_events() -> None:
    """Sim ships 4 ServiceNow events; every one must be present since
    the roadmap set full coverage as the phase 4.5 target."""
    from apps.api.app.node_system.nodes.servicenow.trigger_manifest import MANIFEST

    event_ids = {e.id for e in MANIFEST.events}
    assert event_ids == {
        "incident_created",
        "incident_updated",
        "change_request_created",
        "change_request_updated",
    }


def test_servicenow_credential_registered() -> None:
    from apps.api.app.credential_manager.api_keys import PROVIDERS

    assert "servicenow" in PROVIDERS
    fields = {f.id for f in PROVIDERS["servicenow"].fields}
    assert fields == {"instance", "username", "api_key"}
