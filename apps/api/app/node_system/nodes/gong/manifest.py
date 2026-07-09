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
    RemoteLookup,
)

MANIFEST = ProviderManifest(
    type="action.gong",
    name="Gong",
    category="integration",
    description="Gong.io — call recordings, transcripts, deal insights.",
    icon_slug="gong",
    color="#ffffff",
    base_url="https://api.gong.io/v2",
    credential_type="gong_api_key",
    token_field=["access_key_secret"],
    auth="basic",
    auth_basic_username="{access_key}",
    fields=[
        FieldSpec(name="call_id", label="Call ID", type="string"),
        FieldSpec(
            name="user_id",
            label="User",
            type="string",
            remote=RemoteLookup(provider="gong", resource="users"),
        ),
        FieldSpec(name="deal_id", label="Deal ID", type="string"),
        FieldSpec(name="from_date", label="From Date (ISO)", type="string"),
        FieldSpec(name="to_date", label="To Date (ISO)", type="string"),
        FieldSpec(name="cursor", label="Cursor", type="string", mode="advanced"),
        FieldSpec(name="gong_filter", label="Filter (JSON)", type="json", default={}),
        FieldSpec(name="gong_user_id", label="User ID", type="string"),
        FieldSpec(name="folder_id", label="Library Folder ID", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="phone", label="Phone", type="string"),
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
        OpSpec(
            id="get_extensive_calls",
            label="Get Extensive Calls",
            method="POST",
            path="/v2/calls/extensive",
            visible_fields=["gong_filter"],
            body_builder=lambda v: {"filter": getattr(v, "gong_filter", None) or {}},
        ),
        OpSpec(
            id="aggregate_activity",
            label="Aggregate Activity by Rep",
            method="GET",
            path="/v2/stats/activity/aggregate",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="day_by_day_activity",
            label="Day-by-Day Activity",
            method="GET",
            path="/v2/stats/activity/day-by-day",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="aggregate_by_period",
            label="Aggregate by Period",
            method="GET",
            path="/v2/stats/activity/aggregate-by-period",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="interaction_stats",
            label="Interaction Statistics",
            method="GET",
            path="/v2/stats/interaction",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="answered_scorecards",
            label="List Answered Scorecards",
            method="POST",
            path="/v2/stats/activity/scorecards",
            visible_fields=["gong_filter"],
            body_builder=lambda v: {"filter": getattr(v, "gong_filter", None) or {}},
        ),
        OpSpec(
            id="list_library_folders",
            label="List Library Folders",
            method="GET",
            path="/v2/library/folders",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_folder_content",
            label="Get Library Folder Content",
            method="GET",
            path="/v2/library/folders/{folder_id}/content",
            visible_fields=["folder_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_scorecards",
            label="List Scorecards",
            method="GET",
            path="/v2/settings/scorecards",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_trackers",
            label="List Trackers (topics)",
            method="GET",
            path="/v2/settings/trackers",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_workspaces",
            label="List Workspaces",
            method="GET",
            path="/v2/workspaces",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_flows",
            label="List Flows",
            method="GET",
            path="/v2/flows",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_coaching",
            label="Get Coaching Data",
            method="POST",
            path="/v2/coaching",
            visible_fields=["gong_filter"],
            body_builder=lambda v: {"filter": getattr(v, "gong_filter", None) or {}},
        ),
        OpSpec(
            id="lookup_email",
            label="Lookup Contact by Email",
            method="POST",
            path="/v2/customer/contacts",
            visible_fields=["email"],
            body_builder=lambda v: {"emails": [getattr(v, "email", "") or ""]},
        ),
        OpSpec(
            id="lookup_phone",
            label="Lookup Contact by Phone",
            method="POST",
            path="/v2/customer/contacts/phone",
            visible_fields=["phone"],
            body_builder=lambda v: {"phones": [getattr(v, "phone", "") or ""]},
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
