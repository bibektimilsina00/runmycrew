"""Confluence webhook trigger — manifest form.

Atlassian Cloud sends Confluence webhook deliveries signed with
HMAC-SHA256 hex in `X-Hub-Signature` (with `sha256=` prefix) — same
shape as Jira. Event kind lives in the body's `webhookEvent` field —
scaffold routes via body path.

Full sim parity (22 events): pages (created/updated/moved/removed/
restored/permissions_updated), blogs (created/updated/removed/restored),
comments (created/updated/removed), attachments (created/updated/
removed), labels (added/removed), spaces (created/updated/removed),
users (created).

Setup
  1. Confluence Settings → System → WebHooks.
  2. URL: `${BASE_URL}/api/v1/webhooks/confluence_webhook/${wf}/${node}`.
  3. Configure a secret; paste the same value into this trigger's
     Secret field.
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
    page = body.get("page") or body.get("blogPost") or {}
    space = body.get("space") or {}
    comment = body.get("comment") or {}
    attachment = body.get("attachment") or {}
    user_modification = body.get("userAccount") or body.get("user") or {}
    label = body.get("label") or {}
    return {
        "event": event_type or body.get("webhookEvent") or "",
        "delivery": delivery_id or body.get("id") or "",
        "webhookEvent": body.get("webhookEvent"),
        "page_id": page.get("id"),
        "page_title": page.get("title"),
        "page_status": page.get("status"),
        "space_id": space.get("id") or (page.get("space") or {}).get("id"),
        "space_key": space.get("spaceKey")
        or space.get("key")
        or (page.get("space") or {}).get("spaceKey"),
        "space_name": space.get("name"),
        "comment_id": comment.get("id"),
        "attachment_id": attachment.get("id"),
        "attachment_title": attachment.get("title"),
        "label_name": label.get("name"),
        "label_prefix": label.get("prefix"),
        "modified_by": user_modification.get("displayName") or user_modification.get("accountId"),
        "timestamp": body.get("timestamp"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.confluence_webhook",
    name="Confluence",
    description=(
        "Fires when Atlassian Cloud posts a Confluence webhook. Full sim "
        "event parity — pages/blogs/comments/attachments/labels/spaces "
        "create+update+remove+restore + permissions + user_created. "
        "HMAC-SHA256 verified in X-Hub-Signature."
    ),
    icon_slug="confluence",
    color="#ffffff",
    provider="confluence_webhook",
    signature=SignatureSpec(
        scheme="hmac_sha256",
        header_name="X-Hub-Signature",
        secret_field="secret",
        prefix="sha256=",
    ),
    event_header="X-Atlassian-Webhook-Identifier",
    event_body_path="webhookEvent",
    events=[
        WebhookEvent(value="page_created", label="Page Created"),
        WebhookEvent(value="page_updated", label="Page Updated"),
        WebhookEvent(value="page_removed", label="Page Removed"),
        WebhookEvent(value="page_restored", label="Page Restored"),
        WebhookEvent(value="page_moved", label="Page Moved"),
        WebhookEvent(value="page_permissions_updated", label="Page Permissions Updated"),
        WebhookEvent(value="blog_created", label="Blog Post Created"),
        WebhookEvent(value="blog_updated", label="Blog Post Updated"),
        WebhookEvent(value="blog_removed", label="Blog Post Removed"),
        WebhookEvent(value="blog_restored", label="Blog Post Restored"),
        WebhookEvent(value="comment_created", label="Comment Created"),
        WebhookEvent(value="comment_updated", label="Comment Updated"),
        WebhookEvent(value="comment_removed", label="Comment Removed"),
        WebhookEvent(value="attachment_created", label="Attachment Created"),
        WebhookEvent(value="attachment_updated", label="Attachment Updated"),
        WebhookEvent(value="attachment_removed", label="Attachment Removed"),
        WebhookEvent(value="label_added", label="Label Added"),
        WebhookEvent(value="label_removed", label="Label Removed"),
        WebhookEvent(value="space_created", label="Space Created"),
        WebhookEvent(value="space_updated", label="Space Updated"),
        WebhookEvent(value="space_removed", label="Space Removed"),
        WebhookEvent(value="user_created", label="User Created"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "page_id", "type": "number"},
        {"label": "page_title", "type": "string"},
        {"label": "space_key", "type": "string"},
        {"label": "comment_id", "type": "number"},
        {"label": "attachment_id", "type": "number"},
        {"label": "label_name", "type": "string"},
        {"label": "modified_by", "type": "string"},
        {"label": "body", "type": "object"},
    ],
)
