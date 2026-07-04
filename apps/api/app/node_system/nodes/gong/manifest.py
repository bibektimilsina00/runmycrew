"""Gong action node — manifest form.

Gong REST API at `https://api.gong.io/v2`. Basic auth using the
access key as username + access key secret as password —
`auth_basic_username="{access_key}"` pulls the user side from the
credential dict; token_field=["access_key_secret"] provides the pass.

Calls, users, deals CRUD-ish ops.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.gong",
    name="Gong",
    category="integration",
    description="Gong.io — call recordings, transcripts, deal insights.",
    icon_slug="gong",
    color="#1c1c1c",
    base_url="https://api.gong.io/v2",
    credential_type="gong_api_key",
    token_field=["access_key_secret"],
    auth="basic",
    auth_basic_username="{access_key}",
    fields=[
        FieldSpec(name="call_id", label="Call ID", type="string"),
        FieldSpec(name="user_id", label="User ID", type="string"),
        FieldSpec(name="deal_id", label="Deal ID", type="string"),
        FieldSpec(name="from_date", label="From Date (ISO)", type="string"),
        FieldSpec(name="to_date", label="To Date (ISO)", type="string"),
        FieldSpec(name="cursor", label="Cursor", type="string", mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_calls",
            label="List Calls",
            method="GET",
            path="/calls",
            visible_fields=["from_date", "to_date", "cursor"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "fromDateTime": getattr(v, "from_date", None),
                    "toDateTime": getattr(v, "to_date", None),
                    "cursor": getattr(v, "cursor", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_call",
            label="Get Call",
            method="GET",
            path="/calls/{call_id}",
            visible_fields=["call_id"],
        ),
        OpSpec(
            id="get_call_transcript",
            label="Get Call Transcript",
            method="POST",
            path="/calls/transcript",
            visible_fields=["call_id"],
            body_builder=lambda v: {"filter": {"callIds": [getattr(v, "call_id", None) or ""]}},
        ),
        OpSpec(
            id="list_users",
            label="List Users",
            method="GET",
            path="/users",
            visible_fields=["cursor"],
            query_builder=lambda v: {
                k: val for k, val in {"cursor": getattr(v, "cursor", None)}.items() if val
            },
        ),
        OpSpec(
            id="get_user",
            label="Get User",
            method="GET",
            path="/users/{user_id}",
            visible_fields=["user_id"],
        ),
        OpSpec(
            id="list_extensive_calls",
            label="Rich Call Data",
            method="POST",
            path="/calls/extensive",
            visible_fields=["from_date", "to_date"],
            body_builder=lambda v: {
                "filter": {
                    k: val
                    for k, val in {
                        "fromDateTime": getattr(v, "from_date", None),
                        "toDateTime": getattr(v, "to_date", None),
                    }.items()
                    if val is not None
                },
                "contentSelector": {
                    "context": "Extended",
                    "exposedFields": {
                        "parties": True,
                        "content": {"structure": True, "topics": True, "trackers": True},
                    },
                },
            },
        ),
    ],
    outputs_schema=[
        {"label": "callId", "type": "string"},
        {"label": "records", "type": "object"},
        {"label": "calls", "type": "array"},
        {"label": "users", "type": "array"},
        {"label": "callTranscripts", "type": "array"},
    ],
    allow_error=True,
)
