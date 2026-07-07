"""Notion webhook trigger — manifest form.

Notion (2024) delivers events via webhook with HMAC-SHA256 in the
`X-Notion-Signature` header (prefix `sha256=`). Event kind lives in
the body's `type` field (e.g., `page.created`, `page.updated`,
`comment.created`).

URL-verification challenge:
On first delivery Notion sends `{"verification_token": "..."}` and
expects the server to respond 200 with the token echoed. The scaffold's
`challenge_body_key` handles this before signature verification — no
HMAC is possible yet since the token IS the shared secret being
provisioned. After the user copies the token into the trigger's Secret
field, subsequent deliveries verify normally.

Full sim parity (8 events): comment_created, database_created/deleted/
schema_updated, page_content_updated, page_created/deleted/updated.

Setup
  1. Add this trigger to your workflow.
  2. Notion Integrations → Webhooks → Create.
  3. URL: `${BASE_URL}/api/v1/webhooks/notion_webhook/${wf}/${node}`.
  4. Notion pings the URL — receiver 200-echoes the verification token.
  5. Copy the token from the Notion UI into this trigger's Secret field.
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
    entity = body.get("entity") or {}
    data = body.get("data") or {}
    return {
        "event": event_type or body.get("type") or "",
        "delivery": delivery_id or body.get("id") or "",
        "type": body.get("type"),
        "workspace_id": body.get("workspace_id"),
        "workspace_name": body.get("workspace_name"),
        "authors": body.get("authors"),
        "entity_id": entity.get("id"),
        "entity_type": entity.get("type"),
        "parent_type": (data.get("parent") or {}).get("type"),
        "parent_id": (data.get("parent") or {}).get("page_id")
        or (data.get("parent") or {}).get("database_id"),
        "updated_properties": data.get("updated_properties"),
        "updated_blocks": data.get("updated_blocks"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.notion_webhook",
    name="Notion",
    description=(
        "Fires when Notion posts a webhook delivery — pages, databases, "
        "comments. Full sim event parity via body-path routing on `type`. "
        "First delivery is a URL-verification challenge; the scaffold "
        "echoes the token so Notion accepts the endpoint."
    ),
    icon_slug="notion",
    color="#1c1c1c",
    provider="notion_webhook",
    signature=SignatureSpec(
        scheme="hmac_sha256",
        header_name="X-Notion-Signature",
        secret_field="secret",
        prefix="sha256=",
    ),
    event_header="X-Notion-Event",
    event_body_path="type",
    challenge_body_key="verification_token",
    events=[
        WebhookEvent(value="page.created", label="Page Created"),
        WebhookEvent(value="page.updated", label="Page Updated"),
        WebhookEvent(value="page.content_updated", label="Page Content Updated"),
        WebhookEvent(value="page.deleted", label="Page Deleted"),
        WebhookEvent(value="database.created", label="Database Created"),
        WebhookEvent(value="database.schema_updated", label="Database Schema Updated"),
        WebhookEvent(value="database.deleted", label="Database Deleted"),
        WebhookEvent(value="comment.created", label="Comment Created"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "entity_id", "type": "string"},
        {"label": "entity_type", "type": "string"},
        {"label": "parent_id", "type": "string"},
        {"label": "workspace_id", "type": "string"},
        {"label": "authors", "type": "array"},
        {"label": "updated_properties", "type": "array"},
        {"label": "body", "type": "object"},
    ],
)
