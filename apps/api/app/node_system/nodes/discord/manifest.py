"""Discord action node — manifest form.

Discord API v10 at `https://discord.com/api/v10`. Bot token auth via
`Authorization: Bot {token}` header — the scaffold's `header_token`
scheme with a custom value template covers this.

"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.discord",
    name="Discord",
    category="integration",
    description="Discord — messages, channels, guilds, members, roles, webhooks.",
    icon_slug="discord",
    color="#ffffff",
    base_url="https://discord.com/api/v10",
    credential_type="discord_bot_token",
    token_field=["api_key", "bot_token"],
    auth="header_token",
    auth_header_name="Authorization",
    auth_value_template="Bot {token}",
    fields=[
        FieldSpec(name="channel_id", label="Channel ID", type="string"),
        FieldSpec(name="guild_id", label="Guild ID", type="string"),
        FieldSpec(name="user_id", label="User ID", type="string"),
        FieldSpec(name="message_id", label="Message ID", type="string"),
        FieldSpec(name="role_id", label="Role ID", type="string"),
        FieldSpec(name="member_id", label="Member ID", type="string"),
        FieldSpec(name="webhook_id", label="Webhook ID", type="string"),
        FieldSpec(name="webhook_token", label="Webhook Token", type="string"),
        FieldSpec(name="content", label="Message Content", type="string"),
        FieldSpec(name="embed", label="Embed (JSON)", type="json", default={}),
        FieldSpec(name="embeds", label="Embeds (JSON array)", type="json", default=[]),
        FieldSpec(name="channel_name", label="Channel Name", type="string"),
        FieldSpec(
            name="channel_type",
            label="Channel Type (0=text,2=voice,4=category)",
            type="number",
            default=0,
        ),
        FieldSpec(name="role_name", label="Role Name", type="string"),
        FieldSpec(name="role_color", label="Role Color (int)", type="number"),
        FieldSpec(name="role_permissions", label="Role Permissions (string)", type="string"),
        FieldSpec(name="webhook_name", label="Webhook Name", type="string"),
        FieldSpec(name="reason", label="Audit Log Reason", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=50, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="send_message",
            label="Send Message",
            method="POST",
            path="/channels/{channel_id}/messages",
            visible_fields=["channel_id", "content"],
            body_builder=lambda v: {"content": getattr(v, "content", "") or ""},
        ),
        OpSpec(
            id="send_embed",
            label="Send Embed Message",
            method="POST",
            path="/channels/{channel_id}/messages",
            visible_fields=["channel_id", "content", "embed"],
            body_builder=lambda v: {
                "content": getattr(v, "content", None) or "",
                "embeds": [getattr(v, "embed", None) or {}],
            },
        ),
        OpSpec(
            id="get_messages",
            label="Get Channel Messages",
            method="GET",
            path="/channels/{channel_id}/messages",
            visible_fields=["channel_id", "limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 50) or 50)},
        ),
        OpSpec(
            id="delete_message",
            label="Delete Message",
            method="DELETE",
            path="/channels/{channel_id}/messages/{message_id}",
            visible_fields=["channel_id", "message_id"],
        ),
        OpSpec(
            id="get_guild",
            label="Get Guild",
            method="GET",
            path="/guilds/{guild_id}",
            visible_fields=["guild_id"],
        ),
        OpSpec(
            id="get_user",
            label="Get User",
            method="GET",
            path="/users/{user_id}",
            visible_fields=["user_id"],
        ),
        # ─── channels ──────────────────────────────────────────────
        OpSpec(
            id="get_channel",
            label="Get Channel",
            method="GET",
            path="/channels/{channel_id}",
            visible_fields=["channel_id"],
        ),
        OpSpec(
            id="list_guild_channels",
            label="List Guild Channels",
            method="GET",
            path="/guilds/{guild_id}/channels",
            visible_fields=["guild_id"],
        ),
        OpSpec(
            id="create_channel",
            label="Create Guild Channel",
            method="POST",
            path="/guilds/{guild_id}/channels",
            visible_fields=["guild_id", "channel_name", "channel_type"],
            body_builder=lambda v: {
                "name": getattr(v, "channel_name", "") or "",
                "type": int(getattr(v, "channel_type", 0) or 0),
            },
        ),
        OpSpec(
            id="delete_channel",
            label="Delete Channel",
            method="DELETE",
            path="/channels/{channel_id}",
            visible_fields=["channel_id"],
        ),
        # ─── messages depth ────────────────────────────────────────
        OpSpec(
            id="get_message",
            label="Get Message",
            method="GET",
            path="/channels/{channel_id}/messages/{message_id}",
            visible_fields=["channel_id", "message_id"],
        ),
        OpSpec(
            id="edit_message",
            label="Edit Message",
            method="PATCH",
            path="/channels/{channel_id}/messages/{message_id}",
            visible_fields=["channel_id", "message_id", "content", "embeds"],
            body_builder=lambda v: {
                "content": getattr(v, "content", None) or None,
                "embeds": getattr(v, "embeds", None) or None,
            },
        ),
        OpSpec(
            id="add_reaction",
            label="Add Reaction",
            method="PUT",
            path="/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me",
            visible_fields=["channel_id", "message_id", "emoji"],
        ),
        # ─── guild members + roles ─────────────────────────────────
        OpSpec(
            id="list_members",
            label="List Guild Members",
            method="GET",
            path="/guilds/{guild_id}/members",
            visible_fields=["guild_id", "limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 100) or 100)},
        ),
        OpSpec(
            id="get_member",
            label="Get Guild Member",
            method="GET",
            path="/guilds/{guild_id}/members/{user_id}",
            visible_fields=["guild_id", "user_id"],
        ),
        OpSpec(
            id="add_member_role",
            label="Add Role to Member",
            method="PUT",
            path="/guilds/{guild_id}/members/{user_id}/roles/{role_id}",
            visible_fields=["guild_id", "user_id", "role_id"],
        ),
        OpSpec(
            id="remove_member_role",
            label="Remove Role from Member",
            method="DELETE",
            path="/guilds/{guild_id}/members/{user_id}/roles/{role_id}",
            visible_fields=["guild_id", "user_id", "role_id"],
        ),
        OpSpec(
            id="kick_member",
            label="Kick Guild Member",
            method="DELETE",
            path="/guilds/{guild_id}/members/{user_id}",
            visible_fields=["guild_id", "user_id"],
        ),
        OpSpec(
            id="ban_member",
            label="Ban Guild Member",
            method="PUT",
            path="/guilds/{guild_id}/bans/{user_id}",
            visible_fields=["guild_id", "user_id", "reason"],
            body_builder=lambda v: {"reason": getattr(v, "reason", None) or None},
        ),
        OpSpec(
            id="list_roles",
            label="List Guild Roles",
            method="GET",
            path="/guilds/{guild_id}/roles",
            visible_fields=["guild_id"],
        ),
        OpSpec(
            id="create_role",
            label="Create Role",
            method="POST",
            path="/guilds/{guild_id}/roles",
            visible_fields=["guild_id", "role_name", "role_color", "role_permissions"],
            body_builder=lambda v: {
                "name": getattr(v, "role_name", "") or "",
                "color": int(getattr(v, "role_color", 0) or 0),
                "permissions": getattr(v, "role_permissions", None) or None,
            },
        ),
        OpSpec(
            id="delete_role",
            label="Delete Role",
            method="DELETE",
            path="/guilds/{guild_id}/roles/{role_id}",
            visible_fields=["guild_id", "role_id"],
        ),
        # ─── webhooks ──────────────────────────────────────────────
        OpSpec(
            id="list_channel_webhooks",
            label="List Channel Webhooks",
            method="GET",
            path="/channels/{channel_id}/webhooks",
            visible_fields=["channel_id"],
        ),
        OpSpec(
            id="create_webhook",
            label="Create Channel Webhook",
            method="POST",
            path="/channels/{channel_id}/webhooks",
            visible_fields=["channel_id", "webhook_name"],
            body_builder=lambda v: {"name": getattr(v, "webhook_name", "") or ""},
        ),
        OpSpec(
            id="execute_webhook",
            label="Execute Webhook",
            method="POST",
            path="/webhooks/{webhook_id}/{webhook_token}",
            visible_fields=["webhook_id", "webhook_token", "content", "embeds"],
            body_builder=lambda v: {
                "content": getattr(v, "content", None) or None,
                "embeds": getattr(v, "embeds", None) or None,
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
