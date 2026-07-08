"""Twilio Voice action node — Twilio Voice — outbound calls + call log lookup.

REST at https://api.twilio.com/2010-04-01/Accounts/{account_sid}. See sim-parity roadmap Phase 4.31.
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.twilio.twilio_voice import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.twilio_voice",
    name=NAME,
    category="integration",
    description="Twilio Voice — outbound calls + call log lookup.",
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://api.twilio.com/2010-04-01/Accounts/{account_sid}",
    credential_type="twilio_credentials",
    token_field=["api_key"],
    auth="basic",
    auth_basic_username="{account_sid}",
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
            id="create_call",
            label="Place Outbound Call",
            method="POST",
            path="/Calls.json",
            visible_fields=["to", "from_number", "url"],
            body_builder=lambda v: {
                "To": getattr(v, "to", "") or "",
                "From": getattr(v, "from_number", "") or "",
                "Url": getattr(v, "url", "") or "",
            },
        ),
        OpSpec(
            id="get_call",
            label="Get Call",
            method="GET",
            path="/Calls/{call_sid}.json",
            visible_fields=["call_sid"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_calls",
            label="List Recent Calls",
            method="GET",
            path="/Calls.json",
            visible_fields=["status"],
            query_builder=lambda v: {
                k: val for k, val in {"Status": getattr(v, "status", None) or None}.items() if val
            },
        ),
        OpSpec(
            id="update_call",
            label="Update / Redirect Call",
            method="POST",
            path="/Calls/{call_sid}.json",
            visible_fields=["call_sid", "url", "status"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "Url": getattr(v, "url", None) or None,
                    "Status": getattr(v, "status", None) or None,
                }.items()
                if val is not None
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
