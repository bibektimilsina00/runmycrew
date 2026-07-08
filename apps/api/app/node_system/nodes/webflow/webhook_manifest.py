"""Webflow webhook trigger — manifest form.

Webflow v2 webhooks sign each delivery with HMAC-SHA256 hex of
`{timestamp}:{body}`, where the timestamp lives in the
`x-webflow-timestamp` header (unix milliseconds). Signature ships in
`x-webflow-signature`. Includes a 5-minute anti-replay tolerance
(same practice as Stripe).

Event kind lives on the JSON body under `triggerType`; Webflow doesn't
put it in a header. Deliveries route through the receiver as "any"
unless a proxy lifts `triggerType` into an event header.

Setup
  1. Webflow Site Settings → Integrations → Webhooks → Add Webhook.
  2. URL: `${BASE_URL}/api/v1/webhooks/webflow/${workflow_id}/${node_id}`.
  3. Paste the auto-generated *webhook secret* into this trigger's
     Secret field.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    SignatureSpec,
    WebhookEvent,
    WebhookTriggerManifest,
)


def _shape(payload: Any, event_type: str, delivery_id: str) -> dict[str, Any]:
    body = payload if isinstance(payload, dict) else {}
    trigger_type = body.get("triggerType") or event_type
    payload_data = body.get("payload") or {}
    return {
        "event": trigger_type,
        "delivery": delivery_id or body.get("_id") or "",
        "trigger_type": trigger_type,
        "site_id": body.get("site") or body.get("siteId"),
        "form_id": payload_data.get("formId"),
        "form_name": payload_data.get("name"),
        "form_data": payload_data.get("data"),
        "submission_id": payload_data.get("submissionId"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.webflow_webhook",
    name="Webflow",
    description=(
        "Fires when a Webflow webhook posts a delivery — form submissions, "
        "e-commerce orders, publish events. Signed with HMAC-SHA256 over "
        "timestamp + body under the webhook secret you configured."
    ),
    icon_slug="webflow",
    color="#ffffff",
    provider="webflow",
    signature=SignatureSpec(
        scheme="webflow",
        header_name="x-webflow-signature",
        secret_field="secret",
        prefix="",
    ),
    event_header="X-Webflow-Event",
    extra_fields=[
        FieldSpec(
            name="site_id",
            label="Site ID (display only)",
            type="string",
            placeholder="61...",
            description="Reminder of which Webflow site posts to this trigger.",
        ),
    ],
    events=[
        WebhookEvent(value="form_submission", label="Form Submission"),
        WebhookEvent(value="site_publish", label="Site Publish"),
        WebhookEvent(value="ecomm_new_order", label="New E-comm Order"),
        WebhookEvent(value="ecomm_order_changed", label="E-comm Order Changed"),
        WebhookEvent(value="ecomm_inventory_changed", label="Inventory Changed"),
        WebhookEvent(value="collection_item_created", label="CMS Item Created"),
        WebhookEvent(value="collection_item_changed", label="CMS Item Updated"),
        WebhookEvent(value="collection_item_deleted", label="CMS Item Deleted"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "trigger_type", "type": "string"},
        {"label": "site_id", "type": "string"},
        {"label": "form_id", "type": "string"},
        {"label": "form_name", "type": "string"},
        {"label": "form_data", "type": "object"},
        {"label": "body", "type": "object"},
    ],
)
