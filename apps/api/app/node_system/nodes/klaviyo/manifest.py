"""Klaviyo action node — manifest form.

Klaviyo REST API at `https://a.klaviyo.com/api`. Two custom headers:
  - `Authorization: Klaviyo-API-Key {key}` — not Bearer.
  - `revision: 2024-10-15` — pinned API version.

Profiles + events + lists + segments. JSON:API-style envelopes.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.klaviyo",
    name="Klaviyo",
    category="integration",
    description="Klaviyo — email + SMS marketing, profiles, events, lists.",
    icon_slug="klaviyo",
    color="#1c1c1c",
    base_url="https://a.klaviyo.com/api",
    credential_type="klaviyo_api_key",
    token_field=["api_key"],
    auth="bearer",
    auth_value_template="Klaviyo-API-Key {token}",
    extra_headers={"revision": "2024-10-15", "accept": "application/json"},
    fields=[
        FieldSpec(name="profile_id", label="Profile ID", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="phone_number", label="Phone Number", type="string", mode="advanced"),
        FieldSpec(name="first_name", label="First Name", type="string", mode="advanced"),
        FieldSpec(name="last_name", label="Last Name", type="string", mode="advanced"),
        FieldSpec(name="properties", label="Properties (JSON)", type="json", mode="advanced"),
        FieldSpec(name="event_name", label="Event Metric Name", type="string"),
        FieldSpec(name="event_properties", label="Event Properties (JSON)", type="json"),
        FieldSpec(name="list_id", label="List ID", type="string"),
        FieldSpec(name="segment_id", label="Segment ID", type="string"),
        FieldSpec(name="page_size", label="Page Size", type="number", default=20, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_profiles",
            label="List Profiles",
            method="GET",
            path="/profiles/",
            visible_fields=["page_size"],
            query_builder=lambda v: {"page[size]": int(getattr(v, "page_size", 20) or 20)},
        ),
        OpSpec(
            id="get_profile",
            label="Get Profile",
            method="GET",
            path="/profiles/{profile_id}/",
            visible_fields=["profile_id"],
        ),
        OpSpec(
            id="create_profile",
            label="Create Profile",
            method="POST",
            path="/profiles/",
            visible_fields=["email", "phone_number", "first_name", "last_name", "properties"],
            body_builder=lambda v: {
                "data": {
                    "type": "profile",
                    "attributes": {
                        k: val
                        for k, val in {
                            "email": getattr(v, "email", None),
                            "phone_number": getattr(v, "phone_number", None),
                            "first_name": getattr(v, "first_name", None),
                            "last_name": getattr(v, "last_name", None),
                            "properties": getattr(v, "properties", None),
                        }.items()
                        if val is not None
                    },
                }
            },
        ),
        OpSpec(
            id="update_profile",
            label="Update Profile",
            method="PATCH",
            path="/profiles/{profile_id}/",
            visible_fields=["profile_id", "email", "properties"],
            body_builder=lambda v: {
                "data": {
                    "type": "profile",
                    "id": getattr(v, "profile_id", None) or "",
                    "attributes": {
                        k: val
                        for k, val in {
                            "email": getattr(v, "email", None),
                            "properties": getattr(v, "properties", None),
                        }.items()
                        if val is not None
                    },
                }
            },
        ),
        OpSpec(
            id="create_event",
            label="Track Event",
            method="POST",
            path="/events/",
            visible_fields=["event_name", "email", "event_properties"],
            body_builder=lambda v: {
                "data": {
                    "type": "event",
                    "attributes": {
                        "metric": {
                            "data": {
                                "type": "metric",
                                "attributes": {"name": getattr(v, "event_name", None) or ""},
                            }
                        },
                        "profile": {
                            "data": {
                                "type": "profile",
                                "attributes": {"email": getattr(v, "email", None) or ""},
                            }
                        },
                        "properties": getattr(v, "event_properties", None) or {},
                    },
                }
            },
        ),
        OpSpec(
            id="list_lists",
            label="List Lists",
            method="GET",
            path="/lists/",
        ),
        OpSpec(
            id="get_list",
            label="Get List",
            method="GET",
            path="/lists/{list_id}/",
            visible_fields=["list_id"],
        ),
        OpSpec(
            id="add_profile_to_list",
            label="Add Profile to List",
            method="POST",
            path="/lists/{list_id}/relationships/profiles/",
            visible_fields=["list_id", "profile_id"],
            body_builder=lambda v: {
                "data": [{"type": "profile", "id": getattr(v, "profile_id", None) or ""}]
            },
        ),
        OpSpec(
            id="list_segments",
            label="List Segments",
            method="GET",
            path="/segments/",
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "attributes", "type": "object"},
        {"label": "id", "type": "string"},
        {"label": "links", "type": "object"},
    ],
    allow_error=True,
)
