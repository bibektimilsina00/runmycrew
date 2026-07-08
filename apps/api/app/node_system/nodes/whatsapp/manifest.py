"""WhatsApp Business action node — WhatsApp Business Cloud API — send template + text messages.

REST at https://graph.facebook.com/v21.0. See sim-parity roadmap Phase 4.31.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.whatsapp",
    name="WhatsApp Business",
    category="integration",
    description="WhatsApp Business Cloud API — send template + text messages.",
    icon_slug="whatsapp",
    color="#ffffff",
    base_url="https://graph.facebook.com/v21.0",
    credential_type="whatsapp_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="phone_number_id", label="Phone Number ID", type="string"),
        FieldSpec(name="to", label="To", type="string"),
        FieldSpec(name="text_body", label="Text Body", type="string"),
        FieldSpec(name="template_name", label="Template Name", type="string"),
        FieldSpec(name="language_code", label="Language Code", type="string", default="en_US"),
        FieldSpec(
            name="media_type",
            label="Media Type (image|video|document|audio)",
            type="string",
            default="image",
        ),
        FieldSpec(name="media_link", label="Media URL", type="string"),
        FieldSpec(name="caption", label="Caption", type="string"),
        FieldSpec(name="from_number", label="From (E.164)", type="string"),
        FieldSpec(name="url", label="TwiML URL", type="string"),
        FieldSpec(name="call_sid", label="Call SID", type="string"),
        FieldSpec(name="status", label="Status", type="string"),
        FieldSpec(name="query", label="Query", type="string"),
        FieldSpec(
            name="max_results", label="Max Results", type="number", default=10, mode="advanced"
        ),
        FieldSpec(name="sort_by", label="Sort By", type="string", default="relevance"),
        FieldSpec(name="sort_order", label="Sort Order", type="string", default="descending"),
        FieldSpec(name="arxiv_ids", label="arXiv IDs (JSON array)", type="json", default=[]),
    ],
    operations=[
        OpSpec(
            id="send_text",
            label="Send Text Message",
            method="POST",
            path="/{phone_number_id}/messages",
            visible_fields=["phone_number_id", "to", "text_body"],
            body_builder=lambda v: {
                "messaging_product": "whatsapp",
                "to": getattr(v, "to", "") or "",
                "type": "text",
                "text": {"body": getattr(v, "text_body", "") or ""},
            },
        ),
        OpSpec(
            id="send_template",
            label="Send Template Message",
            method="POST",
            path="/{phone_number_id}/messages",
            visible_fields=["phone_number_id", "to", "template_name", "language_code"],
            body_builder=lambda v: {
                "messaging_product": "whatsapp",
                "to": getattr(v, "to", "") or "",
                "type": "template",
                "template": {
                    "name": getattr(v, "template_name", "") or "",
                    "language": {"code": getattr(v, "language_code", None) or "en_US"},
                },
            },
        ),
        OpSpec(
            id="send_media",
            label="Send Media Message",
            method="POST",
            path="/{phone_number_id}/messages",
            visible_fields=["phone_number_id", "to", "media_type", "media_link", "caption"],
            body_builder=lambda v: {
                "messaging_product": "whatsapp",
                "to": getattr(v, "to", "") or "",
                "type": getattr(v, "media_type", "image") or "image",
                (getattr(v, "media_type", "image") or "image"): {
                    "link": getattr(v, "media_link", "") or "",
                    "caption": getattr(v, "caption", None) or None,
                },
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
