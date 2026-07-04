"""Calendly polling trigger — manifest form.

Watches scheduled events for an organization/user. Calendly's
`/scheduled_events` endpoint requires either `organization` or `user`
URI — user provides via the manifest field.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)


def _flatten_event(item):
    return {
        "uri": item.get("uri"),
        "name": item.get("name"),
        "status": item.get("status"),
        "start_time": item.get("start_time"),
        "end_time": item.get("end_time"),
        "event_type": item.get("event_type"),
        "created_at": item.get("created_at"),
        "location": item.get("location"),
    }


register_flatten("calendly.event", _flatten_event)


MANIFEST = PollingTriggerManifest(
    type="trigger.calendly",
    name="Calendly",
    description="Poll Calendly for new scheduled events (or cancellations).",
    icon_slug="calendly",
    color="#1c1c1c",
    base_url="https://api.calendly.com",
    credential_type="calendly_oauth",
    token_field=["access_token"],
    auth="bearer",
    provider="calendly",
    default_poll_interval_seconds=60,
    common_fields=[
        FieldSpec(
            name="organization",
            label="Organization URI",
            type="string",
            required=True,
            placeholder="https://api.calendly.com/organizations/AAA",
        ),
        FieldSpec(
            name="user",
            label="User URI (optional; leave blank for org-wide)",
            type="string",
            mode="advanced",
        ),
        FieldSpec(
            name="limit",
            label="Count",
            type="number",
            default=20,
            mode="advanced",
        ),
    ],
    events=[
        PollingEvent(
            id="new_event",
            label="New Scheduled Event",
            list_path="/scheduled_events",
            list_params={
                "organization": "{organization}",
                "user": "{user}",
                "status": "active",
                "count": "{limit}",
                "sort": "created_at:desc",
            },
            strategy="known_ids",
            id_field="uri",
            flatten="calendly.event",
        ),
        PollingEvent(
            id="canceled_event",
            label="Canceled Event",
            list_path="/scheduled_events",
            list_params={
                "organization": "{organization}",
                "user": "{user}",
                "status": "canceled",
                "count": "{limit}",
                "sort": "created_at:desc",
            },
            strategy="known_ids",
            id_field="uri",
            flatten="calendly.event",
        ),
    ],
    outputs_schema=[
        {"label": "uri", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "start_time", "type": "string"},
        {"label": "end_time", "type": "string"},
    ],
)
