"""Jira webhook trigger — manifest form.

Atlassian Cloud sends webhook deliveries signed with HMAC-SHA256 hex
in `X-Hub-Signature` (with `sha256=` prefix). Event kind lives in the
JSON body's `webhookEvent` field — the scaffold's body-path routing
extracts it.

Full sim event parity (14 events): issue_created/updated/deleted,
issue_commented, comment_updated/deleted, worklog_created/updated/
deleted, sprint_created/started/closed, version_released,
project_created.

Setup
  1. Add this trigger to your workflow.
  2. Jira Settings → System → WebHooks (Atlassian Cloud path).
  3. URL: `${BASE_URL}/api/v1/webhooks/jira_webhook/${wf}/${node}`.
  4. Configure a secret; paste the same value into this trigger's
     Secret field.
  5. Tick the events you want.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.node_system.scaffolds import (
    SignatureSpec,
    WebhookEvent,
    WebhookTriggerManifest,
)


def _shape(payload: Any, event_type: str, delivery_id: str) -> dict[str, Any]:
    body = payload if isinstance(payload, dict) else {}
    issue = body.get("issue") or {}
    fields = issue.get("fields") or {}
    comment = body.get("comment") or {}
    worklog = body.get("worklog") or {}
    sprint = body.get("sprint") or {}
    user = body.get("user") or {}
    return {
        "event": event_type or body.get("webhookEvent") or "",
        "delivery": delivery_id or "",
        "webhookEvent": body.get("webhookEvent"),
        "issue_event_type": body.get("issue_event_type_name"),
        "issue_key": issue.get("key"),
        "issue_id": issue.get("id"),
        "summary": fields.get("summary"),
        "status": (fields.get("status") or {}).get("name"),
        "priority": (fields.get("priority") or {}).get("name"),
        "assignee": (fields.get("assignee") or {}).get("displayName"),
        "reporter": (fields.get("reporter") or {}).get("displayName"),
        "comment_id": comment.get("id"),
        "comment_body": comment.get("body"),
        "worklog_id": worklog.get("id"),
        "worklog_time_spent": worklog.get("timeSpent"),
        "sprint_id": sprint.get("id"),
        "sprint_name": sprint.get("name"),
        "user_name": user.get("displayName"),
        "user_email": user.get("emailAddress"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.jira_webhook",
    name="Jira",
    description=(
        "Fires when Atlassian Cloud posts a Jira webhook. Full sim event "
        "parity — issue/comment/worklog/sprint create+update+delete, "
        "version_released, project_created. HMAC-SHA256 verified against "
        "the shared secret."
    ),
    icon_slug="jira",
    color="#1c1c1c",
    provider="jira_webhook",
    signature=SignatureSpec(
        scheme="hmac_sha256",
        header_name="X-Hub-Signature",
        secret_field="secret",
        prefix="sha256=",
    ),
    # Jira Cloud doesn't send an event header — event kind lives in
    # the JSON body's `webhookEvent` field. Fallback via body path.
    event_header="X-Atlassian-Webhook-Identifier",
    event_body_path="webhookEvent",
    events=[
        WebhookEvent(value="jira:issue_created", label="Issue Created"),
        WebhookEvent(value="jira:issue_updated", label="Issue Updated"),
        WebhookEvent(value="jira:issue_deleted", label="Issue Deleted"),
        WebhookEvent(value="comment_created", label="Comment Created"),
        WebhookEvent(value="comment_updated", label="Comment Updated"),
        WebhookEvent(value="comment_deleted", label="Comment Deleted"),
        WebhookEvent(value="worklog_created", label="Worklog Created"),
        WebhookEvent(value="worklog_updated", label="Worklog Updated"),
        WebhookEvent(value="worklog_deleted", label="Worklog Deleted"),
        WebhookEvent(value="sprint_created", label="Sprint Created"),
        WebhookEvent(value="sprint_started", label="Sprint Started"),
        WebhookEvent(value="sprint_closed", label="Sprint Closed"),
        WebhookEvent(value="jira:version_released", label="Version Released"),
        WebhookEvent(value="project_created", label="Project Created"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "issue_key", "type": "string"},
        {"label": "issue_id", "type": "string"},
        {"label": "summary", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "assignee", "type": "string"},
        {"label": "comment_body", "type": "string"},
        {"label": "worklog_time_spent", "type": "string"},
        {"label": "sprint_name", "type": "string"},
        {"label": "user_email", "type": "string"},
        {"label": "body", "type": "object"},
    ],
)
