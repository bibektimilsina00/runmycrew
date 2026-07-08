"""Unit tests for Phase 4.10 jira + linear webhook triggers.

Covers:
  - Scaffold extension for list-form event_body_path (Linear's
    composite `{type}.{action}` event kind)
  - Jira webhook payload_shape (issue/comment/worklog/sprint hoist)
  - Linear webhook payload_shape (data.* hoisting through type +
    action variance)
"""

from __future__ import annotations

from apps.api.app.features.webhooks.service import _extract_body_path
from apps.api.app.node_system.nodes.atlassian.jira.webhook_manifest import (
    MANIFEST as JIRA,
)
from apps.api.app.node_system.nodes.atlassian.jira.webhook_manifest import (
    _shape as jira_shape,
)
from apps.api.app.node_system.nodes.linear.webhook_manifest import (
    MANIFEST as LINEAR,
)
from apps.api.app.node_system.nodes.linear.webhook_manifest import (
    _shape as linear_shape,
)

# ── event_body_path routing ─────────────────────────────────────────


def test_jira_body_path_extracts_webhook_event() -> None:
    """Jira Cloud puts `webhookEvent` at the top level. Body-path
    routing must resolve it since Jira doesn't ship an event header."""
    body = {"webhookEvent": "jira:issue_created", "issue": {"key": "ABC-1"}}
    assert _extract_body_path(body, "webhookEvent") == "jira:issue_created"


def test_linear_uses_list_form_body_path() -> None:
    """Linear's event is composed from `type` + `action`. Manifest
    declares a list; scaffold joins with "." — `Issue.create`."""
    assert LINEAR.event_body_path == ["type", "action"]


# ── Jira payload_shape ──────────────────────────────────────────────


def test_jira_shape_hoists_issue_fields() -> None:
    body = {
        "webhookEvent": "jira:issue_updated",
        "issue_event_type_name": "issue_generic",
        "issue": {
            "key": "ABC-42",
            "id": "10042",
            "fields": {
                "summary": "Login broken",
                "status": {"name": "In Progress"},
                "priority": {"name": "High"},
                "assignee": {"displayName": "Alice"},
                "reporter": {"displayName": "Bob"},
            },
        },
        "user": {"displayName": "Carol", "emailAddress": "c@x.io"},
    }
    out = jira_shape(body, "jira:issue_updated", "d1")
    assert out["issue_key"] == "ABC-42"
    assert out["summary"] == "Login broken"
    assert out["status"] == "In Progress"
    assert out["assignee"] == "Alice"
    assert out["user_email"] == "c@x.io"


def test_jira_shape_hoists_comment_worklog_sprint() -> None:
    body = {
        "webhookEvent": "comment_created",
        "comment": {"id": "c1", "body": "LGTM"},
        "worklog": {"id": "w1", "timeSpent": "2h"},
        "sprint": {"id": 3, "name": "Sprint 3"},
    }
    out = jira_shape(body, "comment_created", "d2")
    assert out["comment_body"] == "LGTM"
    assert out["worklog_time_spent"] == "2h"
    assert out["sprint_name"] == "Sprint 3"


def test_jira_manifest_covers_full_sim_event_set() -> None:
    """Sim ships 14 jira trigger events; jira webhook must cover
    all of them (parity target for this PR)."""
    values = {e.value for e in JIRA.events}
    expected = {
        "jira:issue_created",
        "jira:issue_updated",
        "jira:issue_deleted",
        "comment_created",
        "comment_updated",
        "comment_deleted",
        "worklog_created",
        "worklog_updated",
        "worklog_deleted",
        "sprint_created",
        "sprint_started",
        "sprint_closed",
        "jira:version_released",
        "project_created",
    }
    assert expected <= values


# ── Linear payload_shape ────────────────────────────────────────────


def test_linear_shape_composes_event_from_type_and_action() -> None:
    body = {
        "type": "Issue",
        "action": "create",
        "data": {
            "id": "iss1",
            "identifier": "TEA-42",
            "title": "New issue",
            "url": "https://linear.app/x/iss1",
            "state": {"name": "Todo"},
            "assignee": {"name": "Alice"},
            "team": {"key": "TEA"},
        },
    }
    out = linear_shape(body, "Issue.create", "d3")
    assert out["event"] == "Issue.create"
    assert out["type"] == "Issue"
    assert out["action"] == "create"
    assert out["identifier"] == "TEA-42"
    assert out["state_name"] == "Todo"
    assert out["assignee_name"] == "Alice"
    assert out["team_key"] == "TEA"


def test_linear_shape_falls_back_when_receiver_missed_event() -> None:
    """If event_type comes in empty from the receiver (misconfigured
    proxy that strips the routing), the shape recomputes it from body
    so downstream nodes still see the right event string."""
    body = {"type": "Comment", "action": "update", "data": {"id": "cm1"}}
    out = linear_shape(body, "", "d4")
    assert out["event"] == "Comment.update"


def test_linear_shape_survives_missing_data_envelope() -> None:
    """Payload with no `data` shouldn't crash — Linear sometimes ships
    minimal delivery bodies (heartbeats)."""
    body = {"type": "Ping", "action": "test"}
    out = linear_shape(body, "Ping.test", "d5")
    assert out["event"] == "Ping.test"
    assert out["id"] is None


def test_linear_manifest_covers_key_sim_events() -> None:
    """Linear parity: Issue create/update/remove + Comment + Cycle +
    Project + Label + CustomerRequest = the 13 poll-observable +
    delete-only events."""
    values = {e.value for e in LINEAR.events}
    expected = {
        "Issue.create",
        "Issue.update",
        "Issue.remove",
        "Comment.create",
        "Comment.update",
        "Cycle.create",
        "Cycle.update",
        "Project.create",
        "ProjectUpdate.create",
        "IssueLabel.create",
        "IssueLabel.update",
        "CustomerRequest.create",
        "CustomerRequest.update",
    }
    assert expected <= values
