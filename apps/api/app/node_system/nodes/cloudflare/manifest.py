"""Cloudflare action node — manifest form.

Cloudflare's v4 REST API. Bearer auth using a *scoped API token* (not
the legacy global API key). Six ops cover the day-to-day:

  - List zones
  - List / create / update / delete DNS records per zone
  - Purge zone cache
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)

_RECORD_TYPES = ["A", "AAAA", "CNAME", "TXT", "MX", "NS", "SRV", "CAA"]

MANIFEST = ProviderManifest(
    type="action.cloudflare",
    name="Cloudflare",
    category="integration",
    description="Manage Cloudflare zones, DNS records, and cache.",
    icon_slug="cloudflare",
    color="#ffffff",
    base_url="https://api.cloudflare.com/client/v4",
    credential_type="cloudflare_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(
            name="zone_id",
            label="Zone",
            type="string",
            remote=RemoteLookup(provider="cloudflare", resource="zones"),
        ),
        FieldSpec(name="record_id", label="Record ID", type="string"),
        FieldSpec(
            name="record_type",
            label="Record Type",
            type="options",
            options=[{"label": t, "value": t} for t in _RECORD_TYPES],
        ),
        FieldSpec(name="name", label="Name", type="string", placeholder="@ or sub.example.com"),
        FieldSpec(name="content", label="Content", type="string", placeholder="93.184.216.34"),
        FieldSpec(
            name="ttl",
            label="TTL",
            type="number",
            default=1,
            mode="advanced",
            description="1 = auto",
        ),
        FieldSpec(name="proxied", label="Proxied", type="boolean", default=False, mode="advanced"),
        FieldSpec(name="priority", label="MX Priority", type="number", mode="advanced"),
        FieldSpec(name="purge_everything", label="Purge everything", type="boolean", default=True),
        FieldSpec(name="purge_files", label="URL list (JSON array)", type="json", mode="advanced"),
        FieldSpec(name="limit", label="Per page", type="number", default=50, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_zones",
            label="List Zones",
            method="GET",
            path="/zones",
            visible_fields=["limit"],
            query_builder=lambda props: {"per_page": int(getattr(props, "limit", None) or 50)},
        ),
        OpSpec(
            id="list_dns_records",
            label="List DNS Records",
            method="GET",
            path="/zones/{zone_id}/dns_records",
            visible_fields=["zone_id", "record_type", "name", "limit"],
            query_builder=lambda props: {
                k: v
                for k, v in {
                    "type": getattr(props, "record_type", None),
                    "name": getattr(props, "name", None),
                    "per_page": int(getattr(props, "limit", None) or 50),
                }.items()
                if v not in (None, "")
            },
        ),
        OpSpec(
            id="create_dns_record",
            label="Create DNS Record",
            method="POST",
            path="/zones/{zone_id}/dns_records",
            visible_fields=[
                "zone_id",
                "record_type",
                "name",
                "content",
                "ttl",
                "proxied",
                "priority",
            ],
            body_builder=lambda props: {
                k: v
                for k, v in {
                    "type": getattr(props, "record_type", None),
                    "name": getattr(props, "name", None),
                    "content": getattr(props, "content", None),
                    "ttl": int(getattr(props, "ttl", None) or 1),
                    "proxied": bool(getattr(props, "proxied", False)),
                    "priority": getattr(props, "priority", None),
                }.items()
                if v is not None
            },
        ),
        OpSpec(
            id="update_dns_record",
            label="Update DNS Record",
            method="PUT",
            path="/zones/{zone_id}/dns_records/{record_id}",
            visible_fields=[
                "zone_id",
                "record_id",
                "record_type",
                "name",
                "content",
                "ttl",
                "proxied",
            ],
            body_builder=lambda props: {
                k: v
                for k, v in {
                    "type": getattr(props, "record_type", None),
                    "name": getattr(props, "name", None),
                    "content": getattr(props, "content", None),
                    "ttl": int(getattr(props, "ttl", None) or 1),
                    "proxied": bool(getattr(props, "proxied", False)),
                }.items()
                if v is not None
            },
        ),
        OpSpec(
            id="delete_dns_record",
            label="Delete DNS Record",
            method="DELETE",
            path="/zones/{zone_id}/dns_records/{record_id}",
            visible_fields=["zone_id", "record_id"],
            success_payload_template={"deleted": True, "id": "{record_id}"},
        ),
        OpSpec(
            id="purge_cache",
            label="Purge Cache",
            method="POST",
            path="/zones/{zone_id}/purge_cache",
            visible_fields=["zone_id", "purge_everything", "purge_files"],
            body_builder=lambda props: (
                {"purge_everything": True}
                if getattr(props, "purge_everything", True)
                else {"files": getattr(props, "purge_files", None) or []}
            ),
        ),
    ],
    outputs_schema=[
        {"label": "result", "type": "object"},
        {"label": "success", "type": "boolean"},
        {"label": "errors", "type": "array"},
        {"label": "messages", "type": "array"},
        {"label": "result_info", "type": "object"},
    ],
    allow_error=True,
)
