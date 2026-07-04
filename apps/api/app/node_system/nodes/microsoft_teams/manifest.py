"""Microsoft Teams action node — manifest form.

Graph endpoints at `/v1.0/me/chats`, `/v1.0/teams/{team_id}/channels`,
and `/v1.0/chats/{chat_id}/messages`. Bearer auth via shared
microsoft_oauth credential.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.microsoft_teams",
    name="Microsoft Teams",
    category="integration",
    description="Microsoft Teams — chats, channels, messages.",
    icon_slug="microsoft-teams",
    color="#1c1c1c",
    base_url="https://graph.microsoft.com/v1.0",
    credential_type="microsoft_oauth",
    token_field=["access_token"],
    auth="bearer",
    fields=[
        FieldSpec(name="team_id", label="Team ID", type="string"),
        FieldSpec(name="channel_id", label="Channel ID", type="string"),
        FieldSpec(name="chat_id", label="Chat ID", type="string"),
        FieldSpec(name="message_id", label="Message ID", type="string"),
        FieldSpec(name="content", label="Message Content", type="string"),
        FieldSpec(
            name="content_type",
            label="Content Type",
            type="options",
            default="html",
            mode="advanced",
            options=[{"label": "HTML", "value": "html"}, {"label": "Text", "value": "text"}],
        ),
        FieldSpec(name="limit", label="Limit", type="number", default=25, mode="advanced"),
    ],
    operations=[
        OpSpec(id="list_my_teams", label="List My Teams", method="GET", path="/me/joinedTeams"),
        OpSpec(
            id="list_channels",
            label="List Channels",
            method="GET",
            path="/teams/{team_id}/channels",
            visible_fields=["team_id"],
        ),
        OpSpec(
            id="get_channel",
            label="Get Channel",
            method="GET",
            path="/teams/{team_id}/channels/{channel_id}",
            visible_fields=["team_id", "channel_id"],
        ),
        OpSpec(
            id="send_channel_message",
            label="Send Channel Message",
            method="POST",
            path="/teams/{team_id}/channels/{channel_id}/messages",
            visible_fields=["team_id", "channel_id", "content", "content_type"],
            body_builder=lambda v: {
                "body": {
                    "contentType": getattr(v, "content_type", None) or "html",
                    "content": getattr(v, "content", None) or "",
                }
            },
        ),
        OpSpec(
            id="list_channel_messages",
            label="List Channel Messages",
            method="GET",
            path="/teams/{team_id}/channels/{channel_id}/messages",
            visible_fields=["team_id", "channel_id", "limit"],
            query_builder=lambda v: {"$top": int(getattr(v, "limit", 25) or 25)},
        ),
        OpSpec(id="list_chats", label="List My Chats", method="GET", path="/me/chats"),
        OpSpec(
            id="send_chat_message",
            label="Send Chat Message",
            method="POST",
            path="/chats/{chat_id}/messages",
            visible_fields=["chat_id", "content", "content_type"],
            body_builder=lambda v: {
                "body": {
                    "contentType": getattr(v, "content_type", None) or "html",
                    "content": getattr(v, "content", None) or "",
                }
            },
        ),
        OpSpec(
            id="list_chat_messages",
            label="List Chat Messages",
            method="GET",
            path="/chats/{chat_id}/messages",
            visible_fields=["chat_id", "limit"],
            query_builder=lambda v: {"$top": int(getattr(v, "limit", 25) or 25)},
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "displayName", "type": "string"},
        {"label": "body", "type": "object"},
        {"label": "from", "type": "object"},
        {"label": "value", "type": "array"},
        {"label": "@odata.nextLink", "type": "string"},
    ],
    allow_error=True,
)
