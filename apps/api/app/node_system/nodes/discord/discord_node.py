from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)
DISCORD_API = "https://discord.com/api/v10"


class DiscordProperties(BaseModel):
    credential: str | None = None
    bot_token: str | None = None
    operation: str = "send_message"
    channel_id: str | None = None
    content: str | None = None
    embed: Any | None = None
    guild_id: str | None = None
    user_id: str | None = None
    message_id: str | None = None
    limit: int = 50


class DiscordNode(BaseNode[DiscordProperties]):
    @classmethod
    def get_properties_model(cls): return DiscordProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.discord",
            name="Discord",
            category="integration",
            description="Send messages, manage channels, and interact with Discord servers.",
            icon="si:SiDiscord",
            color="#5865f2",
            properties=[
                {"name": "bot_token", "label": "Bot Token", "type": "string", "required": True, "secret": True, "placeholder": "Bot token from Discord Developer Portal"},
                {"name": "operation", "label": "Operation", "type": "options", "default": "send_message", "options": [
                    {"label": "Send Message", "value": "send_message"},
                    {"label": "Send Embed", "value": "send_embed"},
                    {"label": "Get Channel Messages", "value": "get_messages"},
                    {"label": "Delete Message", "value": "delete_message"},
                    {"label": "Get Guild Info", "value": "get_guild"},
                    {"label": "Get User Info", "value": "get_user"},
                ]},
                {"name": "channel_id", "label": "Channel ID", "type": "string", "required": True, "condition": {"field": "operation", "value": ["send_message", "send_embed", "get_messages", "delete_message"]}},
                {"name": "content", "label": "Message Content", "type": "string", "condition": {"field": "operation", "value": "send_message"}},
                {"name": "embed", "label": "Embed (JSON)", "type": "json", "condition": {"field": "operation", "value": "send_embed"}},
                {"name": "message_id", "label": "Message ID", "type": "string", "condition": {"field": "operation", "value": "delete_message"}},
                {"name": "guild_id", "label": "Guild/Server ID", "type": "string", "condition": {"field": "operation", "value": "get_guild"}},
                {"name": "user_id", "label": "User ID", "type": "string", "condition": {"field": "operation", "value": "get_user"}},
                {"name": "limit", "label": "Limit", "type": "number", "default": 50, "mode": "advanced", "condition": {"field": "operation", "value": "get_messages"}},
            ],
            inputs=1, outputs=1,
            outputs_schema=[{"label": "id", "type": "string"}, {"label": "content", "type": "string"}, {"label": "messages", "type": "array"}],
            allow_error=True,
        )

    def _token(self) -> str | None:
        return self.props.bot_token

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        token = self._token()
        if not token:
            return NodeResult(success=False, error="Discord Bot Token is required.")
        headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
        op = self.props.operation
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if op == "send_message":
                    if not self.props.channel_id: return NodeResult(success=False, error="channel_id required")
                    r = await client.post(f"{DISCORD_API}/channels/{self.props.channel_id}/messages", headers=headers, json={"content": self.props.content or ""})
                    r.raise_for_status(); return NodeResult(success=True, output_data=r.json())
                elif op == "send_embed":
                    if not self.props.channel_id: return NodeResult(success=False, error="channel_id required")
                    payload: dict = {}
                    if self.props.embed: payload["embeds"] = [self.props.embed]
                    r = await client.post(f"{DISCORD_API}/channels/{self.props.channel_id}/messages", headers=headers, json=payload)
                    r.raise_for_status(); return NodeResult(success=True, output_data=r.json())
                elif op == "get_messages":
                    if not self.props.channel_id: return NodeResult(success=False, error="channel_id required")
                    r = await client.get(f"{DISCORD_API}/channels/{self.props.channel_id}/messages", headers=headers, params={"limit": min(self.props.limit, 100)})
                    r.raise_for_status(); return NodeResult(success=True, output_data={"messages": r.json(), "count": len(r.json())})
                elif op == "delete_message":
                    if not self.props.channel_id or not self.props.message_id: return NodeResult(success=False, error="channel_id and message_id required")
                    r = await client.delete(f"{DISCORD_API}/channels/{self.props.channel_id}/messages/{self.props.message_id}", headers=headers)
                    r.raise_for_status(); return NodeResult(success=True, output_data={"deleted": True})
                elif op == "get_guild":
                    if not self.props.guild_id: return NodeResult(success=False, error="guild_id required")
                    r = await client.get(f"{DISCORD_API}/guilds/{self.props.guild_id}", headers=headers)
                    r.raise_for_status(); return NodeResult(success=True, output_data=r.json())
                elif op == "get_user":
                    uid = self.props.user_id or "@me"
                    r = await client.get(f"{DISCORD_API}/users/{uid}", headers=headers)
                    r.raise_for_status(); return NodeResult(success=True, output_data=r.json())
                else:
                    return NodeResult(success=False, error=f"Unknown operation: {op}")
        except httpx.HTTPStatusError as e:
            return NodeResult(success=False, error=f"Discord API error {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            logger.error(f"DiscordNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))
