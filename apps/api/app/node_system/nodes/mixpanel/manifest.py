"""Mixpanel action node — manifest form.

Mixpanel splits ingestion and querying across two hosts. We model
both via per-op absolute URLs (the scaffold falls through to the
absolute path when an op specifies one):

  - Ingestion (`https://api.mixpanel.com`) — track events, set
    user/group profiles, identify (alias) ids. Auth is the project
    token in the body.
  - Query (`https://mixpanel.com/api/2.0`) — service-account Basic
    auth (`username:secret`). Engagement queries, event lookup.

The user picks the auth style the API expects per-op. We default to
Basic with the `username` credential field as the user, `api_secret`
as the password.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.mixpanel",
    name="Mixpanel",
    category="integration",
    description="Mixpanel — event tracking + query engagement and funnels.",
    icon_slug="mixpanel",
    color="#ffffff",
    base_url="https://mixpanel.com/api/2.0",
    credential_type="mixpanel_api_key",
    token_field=["api_secret"],
    auth="basic",
    auth_basic_username="{username}",
    fields=[
        FieldSpec(name="event", label="Event name", type="string", placeholder="Signed Up"),
        FieldSpec(name="distinct_id", label="Distinct ID", type="string"),
        FieldSpec(name="properties", label="Properties (JSON)", type="json"),
        FieldSpec(name="set_properties", label="Set Properties (JSON)", type="json"),
        FieldSpec(name="alias", label="Alias", type="string", mode="advanced"),
        FieldSpec(name="from_date", label="From (YYYY-MM-DD)", type="string"),
        FieldSpec(name="to_date", label="To (YYYY-MM-DD)", type="string"),
        FieldSpec(name="where", label="Where clause", type="string", mode="advanced"),
        FieldSpec(name="project_token", label="Project Token", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=100, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="track_event",
            label="Track Event",
            method="POST",
            path="https://api.mixpanel.com/track",
            visible_fields=["event", "distinct_id", "properties", "project_token"],
            body_builder=lambda v: {
                "event": getattr(v, "event", None),
                "properties": {
                    "token": getattr(v, "project_token", None),
                    "distinct_id": getattr(v, "distinct_id", None),
                    **(getattr(v, "properties", None) or {}),
                },
            },
        ),
        OpSpec(
            id="set_profile",
            label="Set User Profile",
            method="POST",
            path="https://api.mixpanel.com/engage",
            visible_fields=["distinct_id", "set_properties", "project_token"],
            body_builder=lambda v: {
                "$token": getattr(v, "project_token", None),
                "$distinct_id": getattr(v, "distinct_id", None),
                "$set": getattr(v, "set_properties", None) or {},
            },
        ),
        OpSpec(
            id="alias_user",
            label="Alias User",
            method="POST",
            path="https://api.mixpanel.com/track",
            visible_fields=["distinct_id", "alias", "project_token"],
            body_builder=lambda v: {
                "event": "$create_alias",
                "properties": {
                    "token": getattr(v, "project_token", None),
                    "distinct_id": getattr(v, "distinct_id", None),
                    "alias": getattr(v, "alias", None),
                },
            },
        ),
        OpSpec(
            id="query_events",
            label="Query Events",
            method="GET",
            path="/export",
            visible_fields=["from_date", "to_date", "event", "where"],
            query_fields=["from_date", "to_date", "event", "where"],
        ),
        OpSpec(
            id="query_engage",
            label="Query Engage (Users)",
            method="GET",
            path="/engage",
            visible_fields=["where", "limit"],
            query_fields=["where", "limit"],
        ),
    ],
    outputs_schema=[
        {"label": "status", "type": "number"},
        {"label": "error", "type": "string"},
        {"label": "results", "type": "array"},
        {"label": "page", "type": "number"},
        {"label": "session_id", "type": "string"},
    ],
    allow_error=True,
)
