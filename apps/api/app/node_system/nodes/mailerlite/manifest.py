"""MailerLite action node — manifest form.

MailerLite v3 REST API at `https://connect.mailerlite.com/api`. Bearer
auth via API token. Subscribers, groups, campaigns, automations.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)

MANIFEST = ProviderManifest(
    type="action.mailerlite",
    name="MailerLite",
    category="integration",
    description="MailerLite — subscribers, groups, campaigns, automations.",
    icon_slug="mailerlite",
    color="#ffffff",
    base_url="https://connect.mailerlite.com/api",
    credential_type="mailerlite_api_key",
    token_field=["api_key"],
    auth="bearer",
    extra_headers={"Accept": "application/json"},
    fields=[
        FieldSpec(name="subscriber_id", label="Subscriber ID or Email", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="fields", label="Fields (JSON)", type="json", mode="advanced"),
        FieldSpec(name="groups", label="Group IDs (JSON array)", type="json", mode="advanced"),
        FieldSpec(
            name="group_id",
            label="Group",
            type="string",
            remote=RemoteLookup(provider="mailerlite", resource="groups"),
        ),
        FieldSpec(name="group_name", label="Group Name", type="string"),
        FieldSpec(name="campaign_id", label="Campaign ID", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=25, mode="advanced"),
        FieldSpec(
            name="status",
            label="Status Filter",
            type="options",
            mode="advanced",
            options=[
                {"label": "Active", "value": "active"},
                {"label": "Unsubscribed", "value": "unsubscribed"},
                {"label": "Junk", "value": "junk"},
                {"label": "Bounced", "value": "bounced"},
                {"label": "Unconfirmed", "value": "unconfirmed"},
            ],
        ),
    ],
    operations=[
        OpSpec(
            id="list_subscribers",
            label="List Subscribers",
            method="GET",
            path="/subscribers",
            visible_fields=["status", "limit"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "filter[status]": getattr(v, "status", None),
                    "limit": int(getattr(v, "limit", 25) or 25),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_subscriber",
            label="Get Subscriber",
            method="GET",
            path="/subscribers/{subscriber_id}",
            visible_fields=["subscriber_id"],
        ),
        OpSpec(
            id="create_subscriber",
            label="Create / Upsert Subscriber",
            method="POST",
            path="/subscribers",
            visible_fields=["email", "fields", "groups"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "email": getattr(v, "email", None),
                    "fields": getattr(v, "fields", None),
                    "groups": getattr(v, "groups", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="update_subscriber",
            label="Update Subscriber",
            method="PUT",
            path="/subscribers/{subscriber_id}",
            visible_fields=["subscriber_id", "fields", "groups"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "fields": getattr(v, "fields", None),
                    "groups": getattr(v, "groups", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="delete_subscriber",
            label="Delete Subscriber",
            method="DELETE",
            path="/subscribers/{subscriber_id}",
            visible_fields=["subscriber_id"],
            success_payload_template={"deleted": True, "subscriber_id": "{subscriber_id}"},
        ),
        OpSpec(
            id="list_groups",
            label="List Groups",
            method="GET",
            path="/groups",
        ),
        OpSpec(
            id="create_group",
            label="Create Group",
            method="POST",
            path="/groups",
            visible_fields=["group_name"],
            body_builder=lambda v: {"name": getattr(v, "group_name", None) or ""},
        ),
        OpSpec(
            id="assign_subscriber_to_group",
            label="Assign Subscriber to Group",
            method="POST",
            path="/subscribers/{subscriber_id}/groups/{group_id}",
            visible_fields=["subscriber_id", "group_id"],
        ),
        OpSpec(
            id="list_campaigns",
            label="List Campaigns",
            method="GET",
            path="/campaigns",
        ),
        OpSpec(
            id="get_campaign",
            label="Get Campaign",
            method="GET",
            path="/campaigns/{campaign_id}",
            visible_fields=["campaign_id"],
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
        {"label": "email", "type": "string"},
        {"label": "meta", "type": "object"},
        {"label": "links", "type": "object"},
    ],
    allow_error=True,
)
