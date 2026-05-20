from typing import Any

from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)


class SlackProperties(BaseModel):
    authentication: str = "fuse_bot"
    credential: str | None = None
    bot_token: str | None = None
    selectBy: str = "channel"
    messageFormat: str = "text"
    operation: str = "send_message"
    channel: str | None = None
    text: str | None = None
    user: str | None = None
    thread_ts: str | None = None
    blocks: Any | None = None
    attachments: Any | None = None
    channel_name: str | None = None
    is_private: bool = False
    limit: int = 100
    ts: str | None = None
    message_ts: str | None = None
    name: str | None = None
    users: str | list[str] | None = None
    include_num_members: bool = True
    trigger_id: str | None = None
    view: Any | None = None
    view_id: str | None = None
    external_id: str | None = None
    hash: str | None = None
    cursor: str | None = None
    include_deleted: bool = False


class SlackNode(BaseNode[SlackProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.slack",
            name="Slack",
            category="integration",
            description="Complete Slack integration: messaging, channels, users, reactions, and modals.",
            icon="MessageSquare",
            color="#4a154b",
            properties=[
                {
                    "name": "authentication",
                    "label": "Authentication",
                    "type": "options",
                    "default": "fuse_bot",
                    "options": [
                        {"label": "Fuse Bot (OAuth)", "value": "fuse_bot"},
                        {"label": "Custom Bot (Token)", "value": "custom_bot"},
                    ],
                },
                {
                    "name": "credential",
                    "label": "Slack Account",
                    "type": "credential",
                    "credentialType": "slack_oauth",
                    "required": True,
                    "condition": {"field": "authentication", "value": "fuse_bot"},
                },
                {
                    "name": "bot_token",
                    "label": "Bot Token",
                    "type": "string",
                    "required": True,
                    "secret": True,
                    "placeholder": "xoxb-...",
                    "condition": {"field": "authentication", "value": "custom_bot"},
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "send_message",
                    "options": [
                        {"label": "Send Message", "value": "send_message"},
                        {"label": "Update Message", "value": "update_message"},
                        {"label": "Delete Message", "value": "delete_message"},
                        {"label": "Send Ephemeral Message", "value": "send_ephemeral"},
                        {"label": "List Channels", "value": "list_channels"},
                        {"label": "Get Channel Info", "value": "get_channel_info"},
                        {"label": "Create Channel", "value": "create_channel"},
                        {"label": "List Channel Members", "value": "list_members"},
                        {"label": "Invite to Channel", "value": "invite_to_channel"},
                        {"label": "List Users", "value": "list_users"},
                        {"label": "Get User Info", "value": "get_user_info"},
                        {"label": "Get User Presence", "value": "get_user_presence"},
                        {"label": "Add Reaction", "value": "add_reaction"},
                        {"label": "Remove Reaction", "value": "remove_reaction"},
                        {"label": "Open Modal (View)", "value": "open_view"},
                        {"label": "Push Modal (View)", "value": "push_view"},
                        {"label": "Update Modal (View)", "value": "update_view"},
                        {"label": "Publish Home View", "value": "publish_view"},
                        {"label": "Get Message Replies", "value": "get_message"},
                    ],
                },
                {
                    "name": "selectBy",
                    "label": "Destination",
                    "type": "options",
                    "default": "channel",
                    "options": [
                        {"label": "Channel", "value": "channel"},
                        {"label": "User (DM)", "value": "user"},
                    ],
                    "condition": {
                        "field": "operation",
                        "value": [
                            "send_message",
                            "send_ephemeral",
                            "add_reaction",
                            "remove_reaction",
                            "get_message",
                        ],
                    },
                },
                # Channel Field
                {
                    "name": "channel",
                    "label": "Channel ID",
                    "type": "string",
                    "placeholder": "C1234567890",
                    "condition": {
                        "all": [
                            {
                                "field": "operation",
                                "value": [
                                    "send_message",
                                    "update_message",
                                    "delete_message",
                                    "send_ephemeral",
                                    "get_channel_info",
                                    "list_members",
                                    "invite_to_channel",
                                    "add_reaction",
                                    "remove_reaction",
                                    "get_message",
                                ],
                            },
                            {"field": "selectBy", "value": "channel"},
                        ]
                    },
                    "loadOptions": "/integrations/slack/channels",
                    "loadOptionsDependsOn": ["authentication", "credential", "bot_token"],
                },
                {
                    "name": "user",
                    "label": "User ID",
                    "type": "string",
                    "placeholder": "U1234567890",
                    "condition": {
                        "any": [
                            {
                                "field": "operation",
                                "value": ["get_user_info", "get_user_presence", "publish_view"],
                            },
                            {
                                "all": [
                                    {
                                        "field": "operation",
                                        "value": [
                                            "send_message",
                                            "send_ephemeral",
                                            "add_reaction",
                                            "remove_reaction",
                                            "get_message",
                                        ],
                                    },
                                    {"field": "selectBy", "value": "user"},
                                ]
                            },
                        ]
                    },
                    "loadOptions": "/integrations/slack/users",
                    "loadOptionsDependsOn": ["authentication", "credential", "bot_token"],
                },
                {
                    "name": "messageFormat",
                    "label": "Message Format",
                    "type": "options",
                    "default": "text",
                    "options": [
                        {"label": "Plain Text", "value": "text"},
                        {"label": "Block Kit (JSON)", "value": "blocks"},
                    ],
                    "condition": {
                        "field": "operation",
                        "value": ["send_message", "update_message", "send_ephemeral"],
                    },
                },
                # Text Field
                {
                    "name": "text",
                    "label": "Message Text",
                    "type": "string",
                    "condition": {
                        "all": [
                            {
                                "field": "operation",
                                "value": ["send_message", "update_message", "send_ephemeral"],
                            },
                            {"field": "messageFormat", "value": "text"},
                        ]
                    },
                },
                # Blocks Field
                {
                    "name": "blocks",
                    "label": "Blocks (JSON)",
                    "type": "json",
                    "condition": {
                        "all": [
                            {
                                "field": "operation",
                                "value": ["send_message", "update_message", "send_ephemeral"],
                            },
                            {"field": "messageFormat", "value": "blocks"},
                        ]
                    },
                },
                # Timestamp (ts) Field
                {
                    "name": "ts",
                    "label": "Message Timestamp (ts)",
                    "type": "string",
                    "condition": {
                        "field": "operation",
                        "value": [
                            "update_message",
                            "delete_message",
                            "add_reaction",
                            "remove_reaction",
                            "get_message",
                        ],
                    },
                },
                # Multi-User Field
                {
                    "name": "users",
                    "label": "User IDs (comma separated)",
                    "type": "string",
                    "condition": {"field": "operation", "value": "invite_to_channel"},
                },
                # Emoji Name
                {
                    "name": "name",
                    "label": "Emoji/Channel Name",
                    "type": "string",
                    "condition": {
                        "field": "operation",
                        "value": ["add_reaction", "remove_reaction", "create_channel"],
                    },
                },
                # Modal/View Fields
                {
                    "name": "trigger_id",
                    "label": "Trigger ID",
                    "type": "string",
                    "condition": {"field": "operation", "value": ["open_view", "push_view"]},
                },
                {
                    "name": "view",
                    "label": "View Payload (JSON)",
                    "type": "json",
                    "condition": {
                        "field": "operation",
                        "value": ["open_view", "push_view", "update_view", "publish_view"],
                    },
                },
                # Advanced Options
                {
                    "name": "thread_ts",
                    "label": "Thread TS",
                    "type": "string",
                    "mode": "advanced",
                    "condition": {
                        "field": "operation",
                        "value": ["send_message", "send_ephemeral"],
                    },
                },
                {
                    "name": "attachments",
                    "label": "Attachments",
                    "type": "file-list",
                    "mode": "advanced",
                    "condition": {"field": "operation", "value": "send_message"},
                },
                {
                    "name": "limit",
                    "label": "Limit",
                    "type": "number",
                    "default": 100,
                    "mode": "advanced",
                    "condition": {
                        "field": "operation",
                        "value": ["list_channels", "list_members", "list_users"],
                    },
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "ok", "type": "boolean"},
                {"label": "error", "type": "string"},
                {"label": "ts", "type": "string"},
                {"label": "channel", "type": "string"},
                {"label": "message", "type": "object"},
                {"label": "user", "type": "object"},
                {"label": "channels", "type": "array"},
                {"label": "members", "type": "array"},
                {"label": "view", "type": "object"},
            ],
            allow_error=True,
            credential_type="slack_oauth",
            tools=["slack"],
            operation_tool_map={
                "chat.postMessage": "slack_send_message",
                "chat.update": "slack_update_message",
                "chat.delete": "slack_delete_message",
                "conversations.list": "slack_list_channels",
                "conversations.info": "slack_get_channel_info",
            },
        )

    @classmethod
    def get_properties_model(cls) -> type[SlackProperties]:
        return SlackProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        try:
            # Determine which token to use
            access_token = None

            if self.props.authentication == "custom_bot":
                access_token = self.props.bot_token
                if not access_token:
                    return NodeResult(success=False, error="Custom Bot Token is required.")
            else:
                # Use Fuse Bot (OAuth)
                if not self.credential:
                    return NodeResult(
                        success=False,
                        error="Slack credential not found. Please connect your Slack account.",
                    )

                access_token = self.credential.get("access_token")
                if not access_token:
                    return NodeResult(
                        success=False, error="Slack access token missing in credential."
                    )

            from apps.api.app.integrations.slack.service import SlackService

            service = SlackService(access_token=access_token, client=context.http_client)

            op = self.props.operation
            output = {}

            if op == "send_message":
                target = self.props.channel if self.props.selectBy == "channel" else self.props.user
                if not target:
                    return NodeResult(
                        success=False, error="Channel/User is required for send_message"
                    )

                is_blocks = self.props.messageFormat == "blocks"
                if is_blocks:
                    if not self.props.blocks:
                        return NodeResult(
                            success=False,
                            error="Blocks JSON is required when Message Format is 'blocks'",
                        )
                    text = None
                    blocks = self.props.blocks
                else:
                    if not self.props.text:
                        return NodeResult(
                            success=False,
                            error="Message Text is required when Message Format is 'text'",
                        )
                    text = self.props.text
                    blocks = None

                output = await service.send_message(
                    channel=target,
                    text=text,
                    thread_ts=self.props.thread_ts,
                    blocks=blocks,
                    attachments=self.props.attachments,
                )

                # Handle file attachments if any
                if self.props.attachments and context.db:
                    import sqlalchemy as sa

                    from apps.api.app.models.asset import Asset

                    for asset_id in self.props.attachments:
                        result_asset = await context.db.execute(
                            sa.select(Asset).where(Asset.id == asset_id)
                        )
                        asset = result_asset.scalar_one_or_none()
                        if asset:
                            await service.upload_file(
                                channels=target,
                                file=str(asset.file_path),
                                filename=str(asset.name),
                                initial_comment=f"Attached file: {asset.name}",
                            )
            elif op == "update_message":
                if not self.props.channel or not self.props.ts:
                    return NodeResult(
                        success=False,
                        error="Channel and Timestamp (ts) are required for update_message",
                    )

                is_blocks = self.props.messageFormat == "blocks"
                if is_blocks:
                    if not self.props.blocks:
                        return NodeResult(
                            success=False,
                            error="Blocks JSON is required when Message Format is 'blocks'",
                        )
                    text = None
                    blocks = self.props.blocks
                else:
                    if not self.props.text:
                        return NodeResult(
                            success=False,
                            error="Message Text is required when Message Format is 'text'",
                        )
                    text = self.props.text
                    blocks = None

                output = await service.update_message(
                    channel=self.props.channel,
                    ts=self.props.ts,
                    text=text,
                    blocks=blocks,
                )
            elif op == "delete_message":
                if not self.props.channel or not self.props.ts:
                    return NodeResult(
                        success=False,
                        error="Channel and Timestamp (ts) are required for delete_message",
                    )
                output = await service.delete_message(channel=self.props.channel, ts=self.props.ts)
            elif op == "send_ephemeral":
                target = self.props.channel if self.props.selectBy == "channel" else self.props.user
                if not target or not self.props.user:
                    return NodeResult(
                        success=False,
                        error="Channel/User and Recipient (user) are required for send_ephemeral",
                    )

                is_blocks = self.props.messageFormat == "blocks"
                if is_blocks:
                    if not self.props.blocks:
                        return NodeResult(
                            success=False,
                            error="Blocks JSON is required when Message Format is 'blocks'",
                        )
                    text = None
                    blocks = self.props.blocks
                else:
                    if not self.props.text:
                        return NodeResult(
                            success=False,
                            error="Message Text is required when Message Format is 'text'",
                        )
                    text = self.props.text
                    blocks = None

                output = await service.send_ephemeral_message(
                    channel=target,
                    user=self.props.user,
                    text=text,
                    thread_ts=self.props.thread_ts,
                    blocks=blocks,
                )
            elif op == "list_channels":
                output = await service.list_channels(
                    limit=self.props.limit, cursor=self.props.cursor
                )
            elif op == "get_channel_info":
                if not self.props.channel:
                    return NodeResult(
                        success=False, error="Channel is required for get_channel_info"
                    )
                output = await service.get_channel_info(channel=self.props.channel)
            elif op == "create_channel":
                if not self.props.name:
                    return NodeResult(
                        success=False, error="Channel Name (name) is required for create_channel"
                    )
                output = await service.create_channel(
                    name=self.props.name, is_private=self.props.is_private
                )
            elif op == "list_members":
                if not self.props.channel:
                    return NodeResult(success=False, error="Channel is required for list_members")
                output = await service.list_members(
                    channel=self.props.channel, limit=self.props.limit, cursor=self.props.cursor
                )
            elif op == "invite_to_channel":
                if not self.props.channel or not self.props.users:
                    return NodeResult(
                        success=False,
                        error="Channel and User IDs are required for invite_to_channel",
                    )
                users = (
                    self.props.users
                    if isinstance(self.props.users, list)
                    else (self.props.users.split(",") if self.props.users else [])
                )
                output = await service.invite_to_channel(channel=self.props.channel, users=users)
            elif op == "list_users":
                output = await service.list_users(
                    limit=self.props.limit,
                    cursor=self.props.cursor,
                    include_deleted=self.props.include_deleted,
                )
            elif op == "get_user_info":
                if not self.props.user:
                    return NodeResult(success=False, error="User ID is required for get_user_info")
                output = await service.get_user_info(user_id=self.props.user)
            elif op == "get_user_presence":
                if not self.props.user:
                    return NodeResult(
                        success=False, error="User ID is required for get_user_presence"
                    )
                output = await service.get_user_presence(user_id=self.props.user)
            elif op == "add_reaction":
                target = self.props.channel if self.props.selectBy == "channel" else self.props.user
                if not target or not self.props.ts or not self.props.name:
                    return NodeResult(
                        success=False,
                        error="Channel/User, Timestamp (ts), and Name (emoji) are required for add_reaction",
                    )
                output = await service.add_reaction(
                    channel=target, timestamp=self.props.ts, name=self.props.name
                )
            elif op == "remove_reaction":
                target = self.props.channel if self.props.selectBy == "channel" else self.props.user
                if not target or not self.props.ts or not self.props.name:
                    return NodeResult(
                        success=False,
                        error="Channel/User, Timestamp (ts), and Name (emoji) are required for remove_reaction",
                    )
                output = await service.remove_reaction(
                    channel=target, timestamp=self.props.ts, name=self.props.name
                )
            elif op == "open_view":
                if not self.props.trigger_id or not self.props.view:
                    return NodeResult(
                        success=False,
                        error="Trigger ID and View Payload are required for open_view",
                    )
                output = await service.open_view(
                    trigger_id=self.props.trigger_id, view=self.props.view
                )
            elif op == "push_view":
                if not self.props.trigger_id or not self.props.view:
                    return NodeResult(
                        success=False,
                        error="Trigger ID and View Payload are required for push_view",
                    )
                output = await service.push_view(
                    trigger_id=self.props.trigger_id, view=self.props.view
                )
            elif op == "update_view":
                if not self.props.view:
                    return NodeResult(
                        success=False, error="View Payload is required for update_view"
                    )
                output = await service.update_view(
                    view=self.props.view,
                    view_id=self.props.view_id,
                    external_id=self.props.external_id,
                    hash=self.props.hash,
                )
            elif op == "publish_view":
                if not self.props.user or not self.props.view:
                    return NodeResult(
                        success=False,
                        error="User ID and View Payload are required for publish_view",
                    )
                output = await service.publish_view(
                    user_id=self.props.user, view=self.props.view, hash=self.props.hash
                )
            elif op == "get_message":
                target = self.props.channel if self.props.selectBy == "channel" else self.props.user
                if not target or not self.props.ts:
                    return NodeResult(
                        success=False,
                        error="Channel/User and Timestamp (ts) are required for get_message",
                    )
                output = await service.get_message(channel=target, ts=self.props.ts)
            else:
                return NodeResult(success=False, error=f"Unsupported operation: {op}")

            return NodeResult(success=True, output_data=output)
        except ValueError as e:
            error_msg = str(e)
            if "Slack API error:" in error_msg:
                return NodeResult(
                    success=True,
                    output_data={
                        "ok": False,
                        "error": error_msg.replace("Slack API error: ", ""),
                    },
                )
            return NodeResult(success=False, error=error_msg)
        except Exception as e:
            logger.error(f"SlackNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))
