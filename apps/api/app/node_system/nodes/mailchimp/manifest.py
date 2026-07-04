"""Mailchimp action node — manifest form.

Mailchimp v3 API at `https://{dc}.api.mailchimp.com/3.0`. The
data-center suffix (`us14`, `us20`, `eu2` …) is embedded in the API
key after a dash, and also drives the API host. The credential
carries both `api_key` and `dc`; the manifest templates `{dc}` into
the URL, and Basic auth passes any username with `api_key` as password.

Lists (audiences), members, campaigns, tags.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

_HOST = "https://{dc}.api.mailchimp.com/3.0"


MANIFEST = ProviderManifest(
    type="action.mailchimp",
    name="Mailchimp",
    category="integration",
    description="Mailchimp — lists, members, campaigns, tags.",
    icon_slug="mailchimp",
    color="#1c1c1c",
    base_url="",
    credential_type="mailchimp_api_key",
    token_field=["api_key"],
    # Mailchimp Basic auth: any string as user, api_key as password.
    # `anystring` is the community convention.
    auth="basic",
    auth_basic_username="anystring",
    fields=[
        FieldSpec(name="list_id", label="List (Audience) ID", type="string"),
        FieldSpec(name="member_hash", label="Member Hash (MD5 of lowercased email)", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(
            name="status",
            label="Subscription Status",
            type="options",
            default="subscribed",
            options=[
                {"label": "Subscribed", "value": "subscribed"},
                {"label": "Unsubscribed", "value": "unsubscribed"},
                {"label": "Cleaned", "value": "cleaned"},
                {"label": "Pending", "value": "pending"},
            ],
        ),
        FieldSpec(name="merge_fields", label="Merge Fields (JSON)", type="json", mode="advanced"),
        FieldSpec(name="tags", label="Tags (JSON array)", type="json", mode="advanced"),
        FieldSpec(name="campaign_id", label="Campaign ID", type="string"),
        FieldSpec(name="count", label="Count", type="number", default=50, mode="advanced"),
        FieldSpec(name="offset", label="Offset", type="number", default=0, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_lists",
            label="List Audiences",
            method="GET",
            path=_HOST + "/lists",
            visible_fields=["count", "offset"],
            query_fields=["count", "offset"],
        ),
        OpSpec(
            id="get_list",
            label="Get Audience",
            method="GET",
            path=_HOST + "/lists/{list_id}",
            visible_fields=["list_id"],
        ),
        OpSpec(
            id="list_members",
            label="List Members",
            method="GET",
            path=_HOST + "/lists/{list_id}/members",
            visible_fields=["list_id", "count", "offset"],
            query_fields=["count", "offset"],
        ),
        OpSpec(
            id="get_member",
            label="Get Member",
            method="GET",
            path=_HOST + "/lists/{list_id}/members/{member_hash}",
            visible_fields=["list_id", "member_hash"],
        ),
        OpSpec(
            id="add_member",
            label="Add Member",
            method="POST",
            path=_HOST + "/lists/{list_id}/members",
            visible_fields=["list_id", "email", "status", "merge_fields", "tags"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "email_address": getattr(v, "email", None),
                    "status": getattr(v, "status", None) or "subscribed",
                    "merge_fields": getattr(v, "merge_fields", None),
                    "tags": getattr(v, "tags", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="update_member",
            label="Update Member",
            method="PATCH",
            path=_HOST + "/lists/{list_id}/members/{member_hash}",
            visible_fields=["list_id", "member_hash", "status", "merge_fields"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "status": getattr(v, "status", None),
                    "merge_fields": getattr(v, "merge_fields", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="delete_member",
            label="Archive Member",
            method="DELETE",
            path=_HOST + "/lists/{list_id}/members/{member_hash}",
            visible_fields=["list_id", "member_hash"],
            success_payload_template={"archived": True, "member_hash": "{member_hash}"},
        ),
        OpSpec(
            id="list_campaigns",
            label="List Campaigns",
            method="GET",
            path=_HOST + "/campaigns",
            visible_fields=["count", "offset"],
            query_fields=["count", "offset"],
        ),
        OpSpec(
            id="send_campaign",
            label="Send Campaign",
            method="POST",
            path=_HOST + "/campaigns/{campaign_id}/actions/send",
            visible_fields=["campaign_id"],
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "email_address", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "members", "type": "array"},
        {"label": "lists", "type": "array"},
        {"label": "campaigns", "type": "array"},
        {"label": "total_items", "type": "number"},
    ],
    allow_error=True,
)
