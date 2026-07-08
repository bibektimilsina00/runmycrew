"""Cal.com action node — manifest form.

Cal.com v2 REST API at `https://api.cal.com/v2`. Bearer auth via a
Cal.com API key. Bookings + event types + availability.

The v2 API requires a `cal-api-version` header pinning the API
version — we pin to 2024-08-13 (latest stable at the time of
writing).
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.calcom import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.calcom",
    name=NAME,
    category="integration",
    description="Cal.com — bookings, event types, availability, users.",
    icon_slug=ICON_SLUG,
    color=COLOR,
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
        FieldSpec(name="booking_id", label="Booking ID", type="string"),
        FieldSpec(name="booking_body", label="Booking Body (JSON)", type="json", default={}),
        FieldSpec(name="event_type_body", label="Event Type Body (JSON)", type="json", default={}),
        FieldSpec(name="schedule_id", label="Schedule ID", type="string"),
        FieldSpec(name="schedule_body", label="Schedule Body (JSON)", type="json", default={}),
        FieldSpec(name="cancellation_reason", label="Cancellation Reason", type="string"),
        FieldSpec(name="reschedule_reason", label="Reschedule Reason", type="string"),
        FieldSpec(name="start_time", label="Start Time (ISO)", type="string"),
        FieldSpec(name="end_time", label="End Time (ISO)", type="string"),
        FieldSpec(name="username", label="Username", type="string"),
    ],
    operations=[
        OpSpec(
            id="get_me",
            label="Get Current User",
            method="GET",
            path="/me",
        ),
        OpSpec(
            id="list_bookings",
            label="List Bookings",
            method="GET",
            path="/v2/bookings",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_booking",
            label="Create Booking",
            method="POST",
            path="/v2/bookings",
            visible_fields=["booking_body"],
            body_builder=lambda v: getattr(v, "booking_body", None) or {},
        ),
        OpSpec(
            id="get_booking",
            label="Get Booking",
            method="GET",
            path="/v2/bookings/{booking_id}",
            visible_fields=["booking_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="cancel_booking",
            label="Cancel Booking",
            method="POST",
            path="/v2/bookings/{booking_id}/cancel",
            visible_fields=["booking_id", "cancellation_reason"],
            body_builder=lambda v: {
                "cancellationReason": getattr(v, "cancellation_reason", None) or None
            },
        ),
        OpSpec(
            id="reschedule_booking",
            label="Reschedule Booking",
            method="POST",
            path="/v2/bookings/{booking_id}/reschedule",
            visible_fields=["booking_id", "start_time", "reschedule_reason"],
            body_builder=lambda v: {
                "start": getattr(v, "start_time", "") or "",
                "reschedulingReason": getattr(v, "reschedule_reason", None) or None,
            },
        ),
        OpSpec(
            id="confirm_booking",
            label="Confirm Booking",
            method="POST",
            path="/v2/bookings/{booking_id}/confirm",
            visible_fields=["booking_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="decline_booking",
            label="Decline Booking",
            method="POST",
            path="/v2/bookings/{booking_id}/decline",
            visible_fields=["booking_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="create_event_type",
            label="Create Event Type",
            method="POST",
            path="/v2/event-types",
            visible_fields=["event_type_body"],
            body_builder=lambda v: getattr(v, "event_type_body", None) or {},
        ),
        OpSpec(
            id="get_event_type",
            label="Get Event Type",
            method="GET",
            path="/v2/event-types/{event_type_id}",
            visible_fields=["event_type_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_event_types",
            label="List Event Types",
            method="GET",
            path="/v2/event-types",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="update_event_type",
            label="Update Event Type",
            method="PATCH",
            path="/v2/event-types/{event_type_id}",
            visible_fields=["event_type_id", "event_type_body"],
            body_builder=lambda v: getattr(v, "event_type_body", None) or {},
        ),
        OpSpec(
            id="delete_event_type",
            label="Delete Event Type",
            method="DELETE",
            path="/v2/event-types/{event_type_id}",
            visible_fields=["event_type_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_schedule",
            label="Create Schedule",
            method="POST",
            path="/v2/schedules",
            visible_fields=["schedule_body"],
            body_builder=lambda v: getattr(v, "schedule_body", None) or {},
        ),
        OpSpec(
            id="get_schedule",
            label="Get Schedule",
            method="GET",
            path="/v2/schedules/{schedule_id}",
            visible_fields=["schedule_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_schedules",
            label="List Schedules",
            method="GET",
            path="/v2/schedules",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="update_schedule",
            label="Update Schedule",
            method="PATCH",
            path="/v2/schedules/{schedule_id}",
            visible_fields=["schedule_id", "schedule_body"],
            body_builder=lambda v: getattr(v, "schedule_body", None) or {},
        ),
        OpSpec(
            id="delete_schedule",
            label="Delete Schedule",
            method="DELETE",
            path="/v2/schedules/{schedule_id}",
            visible_fields=["schedule_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_default_schedule",
            label="Get Default Schedule",
            method="GET",
            path="/v2/schedules/default",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_slots",
            label="Get Available Slots",
            method="GET",
            path="/v2/slots",
            visible_fields=["event_type_id", "start_time", "end_time"],
            query_builder=lambda v: {
                "eventTypeId": getattr(v, "event_type_id", "") or "",
                "start": getattr(v, "start_time", "") or "",
                "end": getattr(v, "end_time", "") or "",
            },
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
