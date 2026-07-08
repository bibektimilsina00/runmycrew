"""Typeform webhook trigger — manifest form.

Typeform signs webhook deliveries with HMAC-SHA256 base64 in
`Typeform-Signature` (prefix `sha256=`). Uses the shared
`hmac_sha256_b64` scheme.

Sim ships 1 event (`typeform_form_submitted`). Typeform delivers
`form_response.submitted` under body's `event_type`.

Setup
  1. Typeform Admin → Connect → Webhooks → Add Webhook.
  2. URL: `${BASE_URL}/api/v1/webhooks/typeform_webhook/${wf}/${node}`.
  3. Copy the *webhook secret* into this trigger's Secret field.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.node_system.nodes.typeform import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    SignatureSpec,
    WebhookEvent,
    WebhookTriggerManifest,
)


def _flatten_answer(answer: dict) -> dict:
    """Typeform ships each answer as `{field: {id, ref}, type, <type>: value}`.
    Collapse into `{field_id, field_ref, type, value}` — downstream nodes
    can reach the raw value without knowing the type-specific key
    ("text" / "email" / "number" / "boolean" / "choice" / "choices").
    """
    field = answer.get("field") or {}
    kind = str(answer.get("type") or "")
    value: Any = None
    if kind in ("text", "email", "url", "phone_number", "date", "long_text", "short_text"):
        value = answer.get(kind) or answer.get("text")
    elif kind == "number":
        value = answer.get("number")
    elif kind == "boolean":
        value = answer.get("boolean")
    elif kind == "choice":
        choice = answer.get("choice") or {}
        value = choice.get("label") or choice.get("other")
    elif kind == "choices":
        choices = answer.get("choices") or {}
        value = choices.get("labels") or choices.get("ids") or []
    elif kind == "file_url":
        value = answer.get("file_url")
    else:
        value = answer.get(kind)
    return {
        "field_id": field.get("id"),
        "field_ref": field.get("ref"),
        "field_title": field.get("title"),
        "type": kind,
        "value": value,
    }


def _shape(payload: Any, event_type: str, delivery_id: str) -> dict[str, Any]:
    body = payload if isinstance(payload, dict) else {}
    fr = body.get("form_response") or {}
    definition = fr.get("definition") or {}
    hidden = fr.get("hidden") or {}
    answers = fr.get("answers") or []
    return {
        "event": event_type or body.get("event_type") or "",
        "delivery": delivery_id or body.get("event_id") or "",
        "event_type": body.get("event_type"),
        "form_id": definition.get("id"),
        "form_title": definition.get("title"),
        "submitted_at": fr.get("submitted_at"),
        "landed_at": fr.get("landed_at"),
        "response_id": fr.get("response_id"),
        "token": fr.get("token"),
        "hidden": hidden,
        "answers": [_flatten_answer(a) for a in answers if isinstance(a, dict)],
        # Convenience map: field_ref → value. Ref is user-chosen and
        # stable, so downstream nodes can do `answers.email` instead of
        # walking the answers array by index.
        "by_ref": {
            (a.get("field") or {}).get("ref"): _flatten_answer(a).get("value")
            for a in answers
            if isinstance(a, dict) and (a.get("field") or {}).get("ref")
        },
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.typeform_webhook",
    name=NAME,
    description=(
        "Fires when a Typeform is submitted. Verified via HMAC-SHA256 "
        "base64 in `Typeform-Signature`. Answers are flattened into "
        "`answers[]` + a `by_ref` map keyed on field ref for stable access."
    ),
    icon_slug=ICON_SLUG,
    color=COLOR,
    provider="typeform_webhook",
    signature=SignatureSpec(
        scheme="hmac_sha256_b64",
        header_name="Typeform-Signature",
        secret_field="secret",
        prefix="sha256=",
    ),
    event_header="x-typeform-event",
    event_body_path="event_type",
    events=[
        WebhookEvent(value="form_response", label="Form Submitted"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "form_id", "type": "string"},
        {"label": "form_title", "type": "string"},
        {"label": "response_id", "type": "string"},
        {"label": "submitted_at", "type": "string"},
        {"label": "answers", "type": "array"},
        {"label": "by_ref", "type": "object"},
        {"label": "hidden", "type": "object"},
        {"label": "body", "type": "object"},
    ],
)
