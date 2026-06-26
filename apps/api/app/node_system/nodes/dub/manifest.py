"""Dub action node — manifest form.

Dub.co is a link-shortening + analytics platform with a clean REST API
under `https://api.dub.co`. Bearer auth. Six ops cover link CRUD +
analytics + tag management.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.dub",
    name="Dub",
    category="integration",
    description="Short links + click analytics via Dub.co.",
    icon_slug="dub",
    color="#1c1c1c",
    base_url="https://api.dub.co",
    credential_type="dub_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(
            name="url", label="Destination URL", type="string", placeholder="https://example.com"
        ),
        FieldSpec(name="key", label="Short Key (optional)", type="string", mode="advanced"),
        FieldSpec(name="domain", label="Domain", type="string", mode="advanced"),
        FieldSpec(name="link_id", label="Link ID", type="string"),
        FieldSpec(name="title", label="Title", type="string", mode="advanced"),
        FieldSpec(name="description", label="Description", type="string", mode="advanced"),
        FieldSpec(name="expires_at", label="Expires (ISO 8601)", type="string", mode="advanced"),
        FieldSpec(name="tag_ids", label="Tag IDs (JSON array)", type="json", mode="advanced"),
        FieldSpec(
            name="event",
            label="Event",
            type="options",
            default="clicks",
            options=[
                {"label": "Clicks", "value": "clicks"},
                {"label": "Leads", "value": "leads"},
                {"label": "Sales", "value": "sales"},
                {"label": "Composite", "value": "composite"},
            ],
        ),
        FieldSpec(
            name="interval",
            label="Interval",
            type="options",
            default="24h",
            options=[
                {"label": "1h", "value": "1h"},
                {"label": "24h", "value": "24h"},
                {"label": "7d", "value": "7d"},
                {"label": "30d", "value": "30d"},
                {"label": "90d", "value": "90d"},
                {"label": "ytd", "value": "ytd"},
                {"label": "1y", "value": "1y"},
                {"label": "all", "value": "all"},
            ],
        ),
        FieldSpec(
            name="group_by",
            label="Group by",
            type="options",
            mode="advanced",
            options=[
                {"label": "Top links", "value": "top_links"},
                {"label": "Countries", "value": "countries"},
                {"label": "Referers", "value": "referers"},
                {"label": "Devices", "value": "devices"},
                {"label": "Browsers", "value": "browsers"},
                {"label": "OS", "value": "os"},
                {"label": "Timeseries", "value": "timeseries"},
            ],
        ),
    ],
    operations=[
        OpSpec(
            id="create_link",
            label="Create Link",
            method="POST",
            path="/links",
            visible_fields=[
                "url",
                "key",
                "domain",
                "title",
                "description",
                "expires_at",
                "tag_ids",
            ],
            body_fields=["url", "key", "domain", "title", "description", "expires_at", "tag_ids"],
        ),
        OpSpec(
            id="update_link",
            label="Update Link",
            method="PATCH",
            path="/links/{link_id}",
            visible_fields=["link_id", "url", "title", "description", "expires_at", "tag_ids"],
            body_fields=["url", "title", "description", "expires_at", "tag_ids"],
        ),
        OpSpec(
            id="delete_link",
            label="Delete Link",
            method="DELETE",
            path="/links/{link_id}",
            visible_fields=["link_id"],
            success_payload_template={"deleted": True, "id": "{link_id}"},
        ),
        OpSpec(
            id="get_link",
            label="Get Link",
            method="GET",
            path="/links/{link_id}",
            visible_fields=["link_id"],
        ),
        OpSpec(
            id="list_links",
            label="List Links",
            method="GET",
            path="/links",
        ),
        OpSpec(
            id="analytics",
            label="Analytics",
            method="GET",
            path="/analytics",
            visible_fields=["event", "interval", "group_by", "link_id", "domain"],
            query_fields=["event", "interval", "group_by", "domain"],
            query_builder=lambda props: {
                k: v
                for k, v in {
                    "event": getattr(props, "event", None),
                    "interval": getattr(props, "interval", None),
                    "groupBy": getattr(props, "group_by", None),
                    "domain": getattr(props, "domain", None),
                    "linkId": getattr(props, "link_id", None),
                }.items()
                if v not in (None, "")
            },
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "shortLink", "type": "string"},
        {"label": "url", "type": "string"},
        {"label": "clicks", "type": "number"},
        {"label": "items", "type": "array"},
    ],
    allow_error=True,
)
