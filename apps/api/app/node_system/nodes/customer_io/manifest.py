"""Customer.io action node — manifest form.

Customer.io's Track API at `https://track.customer.io/api/v1`. Basic
auth using site_id as username + api_key as password.
`auth_basic_username="{site_id}"` pulls site_id from credential.

Track identifies + events + attributes. Broadcasts and campaigns
live on the App API at api.customer.io — separate surface, skip for
now.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.customer_io",
    name="Customer.io",
    category="integration",
    description="Customer.io — track identifies, events, and attributes.",
    icon_slug="customer-io",
    color="#ffffff",
    base_url="https://track.customer.io/api/v1",
    credential_type="customer_io_api_key",
    token_field=["api_key"],
    auth="basic",
    auth_basic_username="{site_id}",
    fields=[
        FieldSpec(name="customer_id", label="Customer ID", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="attributes", label="Attributes (JSON)", type="json"),
        FieldSpec(name="event_name", label="Event Name", type="string"),
        FieldSpec(name="event_data", label="Event Data (JSON)", type="json"),
        FieldSpec(name="anonymous_id", label="Anonymous ID", type="string", mode="advanced"),
        FieldSpec(name="delivery_id", label="Delivery ID", type="string"),
    ],
    operations=[
        OpSpec(
            id="identify",
            label="Identify Customer",
            method="PUT",
            path="/customers/{customer_id}",
            visible_fields=["customer_id", "email", "attributes"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "email": getattr(v, "email", None),
                    **(getattr(v, "attributes", None) or {}),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="delete_customer",
            label="Delete Customer",
            method="DELETE",
            path="/customers/{customer_id}",
            visible_fields=["customer_id"],
            success_payload_template={"deleted": True, "customer_id": "{customer_id}"},
        ),
        OpSpec(
            id="track_event",
            label="Track Event",
            method="POST",
            path="/customers/{customer_id}/events",
            visible_fields=["customer_id", "event_name", "event_data"],
            body_builder=lambda v: {
                "name": getattr(v, "event_name", None) or "",
                "data": getattr(v, "event_data", None) or {},
            },
        ),
        OpSpec(
            id="track_anonymous_event",
            label="Track Anonymous Event",
            method="POST",
            path="/events",
            visible_fields=["event_name", "event_data", "anonymous_id"],
            body_builder=lambda v: {
                "name": getattr(v, "event_name", None) or "",
                "data": getattr(v, "event_data", None) or {},
                "anonymous_id": getattr(v, "anonymous_id", None),
            },
        ),
        OpSpec(
            id="add_device",
            label="Add Device",
            method="PUT",
            path="/customers/{customer_id}/devices",
            visible_fields=["customer_id", "attributes"],
            body_builder=lambda v: {"device": getattr(v, "attributes", None) or {}},
        ),
        OpSpec(
            id="delete_device",
            label="Delete Device",
            method="DELETE",
            path="/customers/{customer_id}/devices/{delivery_id}",
            visible_fields=["customer_id", "delivery_id"],
            success_payload_template={"deleted": True, "device_id": "{delivery_id}"},
        ),
    ],
    outputs_schema=[
        {"label": "meta", "type": "object"},
        {"label": "customer", "type": "object"},
    ],
    allow_error=True,
)
