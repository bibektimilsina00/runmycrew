"""Calendly action node — manifest form.

Calendly REST API at `https://api.calendly.com`. Bearer auth via
calendly_oauth credential. Read scheduled events, invitees, event
types, plus webhook subscription CRUD.
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.calendly import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.calendly",
    name=NAME,
    category="integration",
    description="Calendly — scheduled events, invitees, event types, webhooks.",
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://api.calendly.com",
    credential_type="calendly_oauth",
    token_field=["access_token"],
    auth="bearer",
    fields=[
        FieldSpec(name="organization", label="Organization URI", type="string"),
        FieldSpec(name="user_uri", label="User URI", type="string"),
        FieldSpec(name="event_uuid", label="Event UUID", type="string"),
        FieldSpec(name="event_uri", label="Event URI", type="string"),
        FieldSpec(
            name="status",
            label="Status",
            type="options",
            mode="advanced",
            options=[
                {"label": "active", "value": "active"},
                {"label": "canceled", "value": "canceled"},
            ],
        ),
        FieldSpec(
            name="min_start_time", label="Min Start Time (ISO)", type="string", mode="advanced"
        ),
        FieldSpec(
            name="max_start_time", label="Max Start Time (ISO)", type="string", mode="advanced"
        ),
        FieldSpec(name="webhook_url", label="Webhook URL", type="string"),
        FieldSpec(name="webhook_uuid", label="Webhook UUID", type="string"),
        FieldSpec(name="events", label="Webhook events (JSON array)", type="json", mode="advanced"),
        FieldSpec(name="limit", label="Count", type="number", default=20, mode="advanced"),
    ],
    operations=[
        OpSpec(id="get_me", label="Get Current User", method="GET", path="/users/me"),
        OpSpec(
            id="list_event_types",
            label="List Event Types",
            method="GET",
            path="/event_types",
            visible_fields=["organization", "user_uri", "limit"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "organization": getattr(v, "organization", None),
                    "user": getattr(v, "user_uri", None),
                    "count": int(getattr(v, "limit", 20) or 20),
                }.items()
                if val
            },
        ),
        OpSpec(
            id="list_events",
            label="List Scheduled Events",
            method="GET",
            path="/scheduled_events",
            visible_fields=[
                "organization",
                "user_uri",
                "status",
                "min_start_time",
                "max_start_time",
                "limit",
            ],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "organization": getattr(v, "organization", None),
                    "user": getattr(v, "user_uri", None),
                    "status": getattr(v, "status", None),
                    "min_start_time": getattr(v, "min_start_time", None),
                    "max_start_time": getattr(v, "max_start_time", None),
                    "count": int(getattr(v, "limit", 20) or 20),
                }.items()
                if val
            },
        ),
        OpSpec(
            id="get_event",
            label="Get Scheduled Event",
            method="GET",
            path="/scheduled_events/{event_uuid}",
            visible_fields=["event_uuid"],
        ),
        OpSpec(
            id="list_invitees",
            label="List Invitees",
            method="GET",
            path="/scheduled_events/{event_uuid}/invitees",
            visible_fields=["event_uuid"],
        ),
        OpSpec(
            id="cancel_event",
            label="Cancel Event",
            method="POST",
            path="/scheduled_events/{event_uuid}/cancellation",
            visible_fields=["event_uuid"],
        ),
        OpSpec(
            id="create_webhook",
            label="Create Webhook Subscription",
            method="POST",
            path="/webhook_subscriptions",
            visible_fields=["webhook_url", "organization", "events"],
            body_builder=lambda v: {
                "url": getattr(v, "webhook_url", None),
                "organization": getattr(v, "organization", None),
                "events": getattr(v, "events", None) or ["invitee.created", "invitee.canceled"],
                "scope": "organization",
            },
        ),
        OpSpec(
            id="delete_webhook",
            label="Delete Webhook",
            method="DELETE",
            path="/webhook_subscriptions/{webhook_uuid}",
            visible_fields=["webhook_uuid"],
            success_payload_template={"deleted": True, "uuid": "{webhook_uuid}"},
        ),
    ],
    outputs_schema=[
        {"label": "resource", "type": "object"},
        {"label": "collection", "type": "array"},
        {"label": "uri", "type": "string"},
        {"label": "pagination", "type": "object"},
    ],
    allow_error=True,
)
