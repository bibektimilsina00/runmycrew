"""Cal.com action node — manifest form.

Cal.com v2 REST API at `https://api.cal.com/v2`. Bearer auth via a
Cal.com API key. Bookings + event types + availability.

The v2 API requires a `cal-api-version` header pinning the API
version — we pin to 2024-08-13 (latest stable at the time of
writing).
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.calcom",
    name="Cal.com",
    category="integration",
    description="Cal.com — bookings, event types, availability, users.",
    icon_slug="calcom",
    color="#1c1c1c",
    base_url="https://api.cal.com/v2",
    credential_type="calcom_api_key",
    token_field=["api_key"],
    auth="bearer",
    extra_headers={"cal-api-version": "2024-08-13"},
    fields=[
        FieldSpec(name="booking_uid", label="Booking UID", type="string"),
        FieldSpec(name="event_type_id", label="Event Type ID", type="number"),
        FieldSpec(name="user_id", label="User ID", type="number"),
        FieldSpec(name="attendee_email", label="Attendee Email", type="string"),
        FieldSpec(name="attendee_name", label="Attendee Name", type="string"),
        FieldSpec(name="start", label="Start (ISO)", type="string"),
        FieldSpec(
            name="time_zone", label="Time Zone", type="string", default="UTC", mode="advanced"
        ),
        FieldSpec(name="language", label="Language", type="string", default="en", mode="advanced"),
        FieldSpec(name="reason", label="Cancellation Reason", type="string"),
        FieldSpec(
            name="status",
            label="Status",
            type="options",
            options=[
                {"label": "Upcoming", "value": "upcoming"},
                {"label": "Past", "value": "past"},
                {"label": "Cancelled", "value": "cancelled"},
            ],
            mode="advanced",
        ),
        FieldSpec(name="take", label="Take", type="number", default=50, mode="advanced"),
        FieldSpec(name="skip", label="Skip", type="number", default=0, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_bookings",
            label="List Bookings",
            method="GET",
            path="/bookings",
            visible_fields=["status", "take", "skip"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "status": getattr(v, "status", None),
                    "take": int(getattr(v, "take", 50) or 50),
                    "skip": int(getattr(v, "skip", 0) or 0),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_booking",
            label="Get Booking",
            method="GET",
            path="/bookings/{booking_uid}",
            visible_fields=["booking_uid"],
        ),
        OpSpec(
            id="create_booking",
            label="Create Booking",
            method="POST",
            path="/bookings",
            visible_fields=[
                "event_type_id",
                "start",
                "attendee_email",
                "attendee_name",
                "time_zone",
                "language",
            ],
            body_builder=lambda v: {
                "eventTypeId": int(getattr(v, "event_type_id", 0) or 0),
                "start": getattr(v, "start", None) or "",
                "attendee": {
                    "name": getattr(v, "attendee_name", None) or "",
                    "email": getattr(v, "attendee_email", None) or "",
                    "timeZone": getattr(v, "time_zone", None) or "UTC",
                    "language": getattr(v, "language", None) or "en",
                },
            },
        ),
        OpSpec(
            id="cancel_booking",
            label="Cancel Booking",
            method="POST",
            path="/bookings/{booking_uid}/cancel",
            visible_fields=["booking_uid", "reason"],
            body_builder=lambda v: {
                "cancellationReason": getattr(v, "reason", None) or "",
            },
        ),
        OpSpec(
            id="reschedule_booking",
            label="Reschedule Booking",
            method="POST",
            path="/bookings/{booking_uid}/reschedule",
            visible_fields=["booking_uid", "start", "reason"],
            body_builder=lambda v: {
                "start": getattr(v, "start", None) or "",
                "reschedulingReason": getattr(v, "reason", None) or "",
            },
        ),
        OpSpec(
            id="list_event_types",
            label="List Event Types",
            method="GET",
            path="/event-types",
            visible_fields=["user_id"],
            query_builder=lambda v: (
                {"username": None, "eventTypeId": None}
                if False
                else {
                    k: val
                    for k, val in {
                        "userId": getattr(v, "user_id", None),
                    }.items()
                    if val is not None
                }
            ),
        ),
        OpSpec(
            id="get_event_type",
            label="Get Event Type",
            method="GET",
            path="/event-types/{event_type_id}",
            visible_fields=["event_type_id"],
        ),
        OpSpec(
            id="get_me",
            label="Get Current User",
            method="GET",
            path="/me",
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "status", "type": "string"},
        {"label": "uid", "type": "string"},
        {"label": "attendees", "type": "array"},
        {"label": "eventType", "type": "object"},
    ],
    allow_error=True,
)
