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
        FieldSpec(name="subscriber_hash", label="Subscriber Hash (MD5 of email)", type="string"),
        FieldSpec(name="email_address", label="Email Address", type="string"),
        FieldSpec(
            name="status_field",
            label="Status (subscribed|unsubscribed|cleaned|pending)",
            type="string",
        ),
        FieldSpec(name="name", label="Name", type="string"),
        FieldSpec(name="from_name", label="From Name", type="string"),
        FieldSpec(name="reply_to", label="Reply-To", type="string"),
        FieldSpec(name="settings_body", label="Campaign Settings (JSON)", type="json", default={}),
        FieldSpec(name="schedule_time", label="Schedule Time (ISO)", type="string"),
        FieldSpec(name="html", label="HTML", type="string"),
        FieldSpec(name="plain_text", label="Plain Text", type="string"),
        FieldSpec(name="workflow_id", label="Workflow ID", type="string"),
        FieldSpec(name="template_id", label="Template ID", type="string"),
        FieldSpec(name="segment_id", label="Segment ID", type="string"),
        FieldSpec(name="segment_name", label="Segment Name", type="string"),
        FieldSpec(
            name="static_segment",
            label="Static Segment Emails (JSON array)",
            type="json",
            default=[],
        ),
        FieldSpec(name="tags_body", label="Tags Body (JSON)", type="json", default={}),
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
        OpSpec(
            id="delete_audience",
            label="Delete Audience",
            method="DELETE",
            path="/lists/{list_id}",
            visible_fields=["list_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="update_audience",
            label="Update Audience",
            method="PATCH",
            path="/lists/{list_id}",
            visible_fields=["list_id", "name", "reply_to", "from_name"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "name": getattr(v, "name", None) or None,
                    "contact": {"from_name": getattr(v, "from_name", None) or None}
                    if getattr(v, "from_name", None)
                    else None,
                    "campaign_defaults": {"reply_to": getattr(v, "reply_to", None) or None}
                    if getattr(v, "reply_to", None)
                    else None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="add_or_update_member",
            label="Add or Update Member",
            method="PUT",
            path="/lists/{list_id}/members/{subscriber_hash}",
            visible_fields=["list_id", "subscriber_hash", "email_address", "status_field"],
            body_builder=lambda v: {
                "email_address": getattr(v, "email_address", "") or "",
                "status_if_new": getattr(v, "status_field", None) or "subscribed",
                "merge_fields": getattr(v, "merge_fields", None) or {},
            },
        ),
        OpSpec(
            id="archive_member",
            label="Archive Member",
            method="DELETE",
            path="/lists/{list_id}/members/{subscriber_hash}",
            visible_fields=["list_id", "subscriber_hash"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="unarchive_member",
            label="Unarchive Member",
            method="POST",
            path="/lists/{list_id}/members/{subscriber_hash}",
            visible_fields=["list_id", "subscriber_hash"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="update_campaign",
            label="Update Campaign",
            method="PATCH",
            path="/campaigns/{campaign_id}",
            visible_fields=["campaign_id", "settings_body"],
            body_builder=lambda v: getattr(v, "settings_body", None) or {},
        ),
        OpSpec(
            id="delete_campaign",
            label="Delete Campaign",
            method="DELETE",
            path="/campaigns/{campaign_id}",
            visible_fields=["campaign_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="schedule_campaign",
            label="Schedule Campaign",
            method="POST",
            path="/campaigns/{campaign_id}/actions/schedule",
            visible_fields=["campaign_id", "schedule_time"],
            body_builder=lambda v: {"schedule_time": getattr(v, "schedule_time", "") or ""},
        ),
        OpSpec(
            id="unschedule_campaign",
            label="Unschedule Campaign",
            method="POST",
            path="/campaigns/{campaign_id}/actions/unschedule",
            visible_fields=["campaign_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="replicate_campaign",
            label="Replicate Campaign",
            method="POST",
            path="/campaigns/{campaign_id}/actions/replicate",
            visible_fields=["campaign_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="get_campaign_content",
            label="Get Campaign Content",
            method="GET",
            path="/campaigns/{campaign_id}/content",
            visible_fields=["campaign_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="set_campaign_content",
            label="Set Campaign Content",
            method="PUT",
            path="/campaigns/{campaign_id}/content",
            visible_fields=["campaign_id", "html", "plain_text"],
            body_builder=lambda v: {
                "html": getattr(v, "html", None) or "",
                "plain_text": getattr(v, "plain_text", None) or "",
            },
        ),
        OpSpec(
            id="get_automations",
            label="List Classic Automations",
            method="GET",
            path="/automations",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_automation",
            label="Get Classic Automation",
            method="GET",
            path="/automations/{workflow_id}",
            visible_fields=["workflow_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="start_automation",
            label="Start Automation",
            method="POST",
            path="/automations/{workflow_id}/actions/start-all-emails",
            visible_fields=["workflow_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="pause_automation",
            label="Pause Automation",
            method="POST",
            path="/automations/{workflow_id}/actions/pause-all-emails",
            visible_fields=["workflow_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="get_templates",
            label="List Templates",
            method="GET",
            path="/templates",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_template",
            label="Get Template",
            method="GET",
            path="/templates/{template_id}",
            visible_fields=["template_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_campaign_reports",
            label="List Campaign Reports",
            method="GET",
            path="/reports",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_campaign_report",
            label="Get Campaign Report",
            method="GET",
            path="/reports/{campaign_id}",
            visible_fields=["campaign_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_segments",
            label="List Segments",
            method="GET",
            path="/lists/{list_id}/segments",
            visible_fields=["list_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_segment",
            label="Get Segment",
            method="GET",
            path="/lists/{list_id}/segments/{segment_id}",
            visible_fields=["list_id", "segment_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_segment",
            label="Create Segment",
            method="POST",
            path="/lists/{list_id}/segments",
            visible_fields=["list_id", "segment_name", "static_segment"],
            body_builder=lambda v: {
                "name": getattr(v, "segment_name", "") or "",
                "static_segment": getattr(v, "static_segment", []) or [],
            },
        ),
        OpSpec(
            id="delete_segment",
            label="Delete Segment",
            method="DELETE",
            path="/lists/{list_id}/segments/{segment_id}",
            visible_fields=["list_id", "segment_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_tags",
            label="List Member Tags",
            method="GET",
            path="/lists/{list_id}/members/{subscriber_hash}/tags",
            visible_fields=["list_id", "subscriber_hash"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="update_member_tags",
            label="Update Member Tags",
            method="POST",
            path="/lists/{list_id}/members/{subscriber_hash}/tags",
            visible_fields=["list_id", "subscriber_hash", "tags_body"],
            body_builder=lambda v: getattr(v, "tags_body", None) or {"tags": []},
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
