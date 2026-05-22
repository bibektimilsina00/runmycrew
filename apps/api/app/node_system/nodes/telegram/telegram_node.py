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


class TelegramProperties(BaseModel):
    bot_token: str | None = None
    operation: str = "send_message"
    chat_id: str | None = None
    text: str | None = None
    parse_mode: str = "HTML"
    photo_url: str | None = None
    document_url: str | None = None
    caption: str | None = None
    reply_to_message_id: str | None = None
    disable_notification: bool = False
    limit: int = 100


class TelegramNode(BaseNode[TelegramProperties]):
    @classmethod
    def get_properties_model(cls): return TelegramProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.telegram",
            name="Telegram",
            category="integration",
            description="Send messages, photos, and documents via a Telegram bot.",
            icon="si:SiTelegram",
            color="#26a5e4",
            properties=[
                {"name": "bot_token", "label": "Bot Token", "type": "string", "required": True, "secret": True, "placeholder": "Token from @BotFather"},
                {"name": "operation", "label": "Operation", "type": "options", "default": "send_message", "options": [
                    {"label": "Send Message", "value": "send_message"},
                    {"label": "Send Photo", "value": "send_photo"},
                    {"label": "Send Document", "value": "send_document"},
                    {"label": "Get Updates", "value": "get_updates"},
                    {"label": "Get Chat Info", "value": "get_chat"},
                ]},
                {"name": "chat_id", "label": "Chat ID", "type": "string", "required": True, "condition": {"field": "operation", "value": ["send_message", "send_photo", "send_document", "get_chat"]}},
                {"name": "text", "label": "Message Text", "type": "string", "condition": {"field": "operation", "value": "send_message"}},
                {"name": "parse_mode", "label": "Parse Mode", "type": "options", "default": "HTML", "options": [{"label": "HTML", "value": "HTML"}, {"label": "Markdown", "value": "Markdown"}, {"label": "Plain", "value": ""}], "condition": {"field": "operation", "value": "send_message"}},
                {"name": "photo_url", "label": "Photo URL", "type": "string", "condition": {"field": "operation", "value": "send_photo"}},
                {"name": "document_url", "label": "Document URL", "type": "string", "condition": {"field": "operation", "value": "send_document"}},
                {"name": "caption", "label": "Caption", "type": "string", "mode": "advanced", "condition": {"field": "operation", "value": ["send_photo", "send_document"]}},
                {"name": "disable_notification", "label": "Silent", "type": "boolean", "default": False, "mode": "advanced"},
                {"name": "limit", "label": "Limit", "type": "number", "default": 100, "mode": "advanced", "condition": {"field": "operation", "value": "get_updates"}},
            ],
            inputs=1, outputs=1,
            outputs_schema=[{"label": "message_id", "type": "number"}, {"label": "chat", "type": "object"}, {"label": "updates", "type": "array"}],
            allow_error=True,
        )

    def _api(self, method: str) -> str:
        return f"https://api.telegram.org/bot{self.props.bot_token}/{method}"

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.bot_token:
            return NodeResult(success=False, error="Bot Token is required.")
        op = self.props.operation
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if op == "send_message":
                    if not self.props.chat_id: return NodeResult(success=False, error="chat_id required")
                    payload: dict = {"chat_id": self.props.chat_id, "text": self.props.text or "", "disable_notification": self.props.disable_notification}
                    if self.props.parse_mode: payload["parse_mode"] = self.props.parse_mode
                    r = await client.post(self._api("sendMessage"), json=payload)
                    r.raise_for_status(); data = r.json(); return NodeResult(success=True, output_data=data.get("result", data))
                elif op == "send_photo":
                    if not self.props.chat_id or not self.props.photo_url: return NodeResult(success=False, error="chat_id and photo_url required")
                    payload = {"chat_id": self.props.chat_id, "photo": self.props.photo_url, "disable_notification": self.props.disable_notification}
                    if self.props.caption: payload["caption"] = self.props.caption
                    r = await client.post(self._api("sendPhoto"), json=payload)
                    r.raise_for_status(); return NodeResult(success=True, output_data=r.json().get("result", {}))
                elif op == "send_document":
                    if not self.props.chat_id or not self.props.document_url: return NodeResult(success=False, error="chat_id and document_url required")
                    payload = {"chat_id": self.props.chat_id, "document": self.props.document_url}
                    if self.props.caption: payload["caption"] = self.props.caption
                    r = await client.post(self._api("sendDocument"), json=payload)
                    r.raise_for_status(); return NodeResult(success=True, output_data=r.json().get("result", {}))
                elif op == "get_updates":
                    r = await client.get(self._api("getUpdates"), params={"limit": min(self.props.limit, 100)})
                    r.raise_for_status(); updates = r.json().get("result", [])
                    return NodeResult(success=True, output_data={"updates": updates, "count": len(updates)})
                elif op == "get_chat":
                    if not self.props.chat_id: return NodeResult(success=False, error="chat_id required")
                    r = await client.get(self._api("getChat"), params={"chat_id": self.props.chat_id})
                    r.raise_for_status(); return NodeResult(success=True, output_data=r.json().get("result", {}))
                else:
                    return NodeResult(success=False, error=f"Unknown operation: {op}")
        except httpx.HTTPStatusError as e:
            return NodeResult(success=False, error=f"Telegram API error {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            logger.error(f"TelegramNode failed: {e}", exc_info=True); return NodeResult(success=False, error=str(e))
