"""Cal.com polling trigger — manifest form.

Watches bookings on a Cal.com account via v2 REST API.
Bearer + cal-api-version header (same shape as the action node).
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)


def _flatten_booking(item):
    return {
        "uid": item.get("uid"),
        "id": item.get("id"),
        "title": item.get("title"),
        "status": item.get("status"),
        "start": item.get("start"),
        "end": item.get("end"),
        "attendees": item.get("attendees"),
        "eventTypeId": item.get("eventTypeId"),
        "cancellationReason": item.get("cancellationReason"),
    }


register_flatten("calcom.booking", _flatten_booking)


MANIFEST = PollingTriggerManifest(
    type="trigger.calcom",
    name="Cal.com",
    description="Poll Cal.com for new / cancelled bookings.",
    icon_slug="calcom",
    color="#1c1c1c",
    base_url="https://api.cal.com/v2",
    credential_type="calcom_api_key",
    token_field=["api_key"],
    auth="bearer",
    extra_headers={"cal-api-version": "2024-08-13"},
    provider="calcom",
    default_poll_interval_seconds=60,
    common_fields=[
        FieldSpec(
            name="event_type_id",
            label="Event Type ID (optional)",
            type="number",
            mode="advanced",
        ),
        FieldSpec(
            name="take",
            label="Take",
            type="number",
            default=25,
            mode="advanced",
        ),
    ],
    events=[
        PollingEvent(
            id="new_booking",
            label="Booking Created",
            list_path="/bookings",
            list_params={
                "status": "upcoming",
                "take": "{take}",
                "sortStart": "desc",
            },
            strategy="known_ids",
            id_field="uid",
            flatten="calcom.booking",
        ),
        PollingEvent(
            id="cancelled_booking",
            label="Booking Cancelled",
            list_path="/bookings",
            list_params={
                "status": "cancelled",
                "take": "{take}",
                "sortStart": "desc",
            },
            strategy="known_ids",
            id_field="uid",
            flatten="calcom.booking",
        ),
    ],
    outputs_schema=[
        {"label": "uid", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "start", "type": "string"},
        {"label": "end", "type": "string"},
    ],
)
