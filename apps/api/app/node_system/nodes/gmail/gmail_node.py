from __future__ import annotations

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)
GMAIL_API = "https://gmail.googleapis.com/gmail/v1"


class GmailProperties(BaseModel):
    credential: str | None = None
    operation: str = "send_email"
    to: str | None = None
    subject: str | None = None
    body: str | None = None
    body_type: str = "plain"
    cc: str | None = None
    bcc: str | None = None
    query: str | None = None
    message_id: str | None = None
    max_results: int = 10


class GmailNode(BaseNode[GmailProperties]):
    @classmethod
    def get_properties_model(cls): return GmailProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.gmail",
            name="Gmail",
            category="integration",
            description="Send emails, search inbox, and manage Gmail messages using OAuth.",
            icon="si:SiGmail",
            color="#ea4335",
            properties=[
                {"name": "credential", "label": "Google Account", "type": "credential", "credentialType": "google_oauth", "required": True},
                {"name": "operation", "label": "Operation", "type": "options", "default": "send_email", "options": [
                    {"label": "Send Email", "value": "send_email"},
                    {"label": "Search Emails", "value": "search"},
                    {"label": "Get Email", "value": "get_email"},
                    {"label": "List Labels", "value": "list_labels"},
                    {"label": "Get Profile", "value": "get_profile"},
                ]},
                {"name": "to", "label": "To", "type": "string", "required": True, "condition": {"field": "operation", "value": "send_email"}},
                {"name": "subject", "label": "Subject", "type": "string", "condition": {"field": "operation", "value": "send_email"}},
                {"name": "body", "label": "Body", "type": "string", "condition": {"field": "operation", "value": "send_email"}},
                {"name": "body_type", "label": "Body Format", "type": "options", "default": "plain", "options": [{"label": "Plain Text", "value": "plain"}, {"label": "HTML", "value": "html"}], "condition": {"field": "operation", "value": "send_email"}, "mode": "advanced"},
                {"name": "cc", "label": "CC", "type": "string", "mode": "advanced", "condition": {"field": "operation", "value": "send_email"}},
                {"name": "bcc", "label": "BCC", "type": "string", "mode": "advanced", "condition": {"field": "operation", "value": "send_email"}},
                {"name": "query", "label": "Search Query", "type": "string", "placeholder": "is:unread from:boss@company.com", "condition": {"field": "operation", "value": "search"}},
                {"name": "max_results", "label": "Max Results", "type": "number", "default": 10, "mode": "advanced", "condition": {"field": "operation", "value": "search"}},
                {"name": "message_id", "label": "Message ID", "type": "string", "condition": {"field": "operation", "value": "get_email"}},
            ],
            inputs=1, outputs=1,
            outputs_schema=[{"label": "id", "type": "string"}, {"label": "threadId", "type": "string"}, {"label": "messages", "type": "array"}, {"label": "snippet", "type": "string"}],
            allow_error=True,
            credential_type="google_oauth",
        )

    def _get_token(self) -> str | None:
        if not self.credential: return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        token = self._get_token()
        if not token: return NodeResult(success=False, error="Google OAuth credential required.")
        headers = {"Authorization": f"Bearer {token}"}
        op = self.props.operation
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if op == "send_email":
                    if not self.props.to: return NodeResult(success=False, error="To address required")
                    msg = MIMEMultipart()
                    msg["to"] = self.props.to
                    msg["subject"] = self.props.subject or ""
                    if self.props.cc: msg["cc"] = self.props.cc
                    if self.props.bcc: msg["bcc"] = self.props.bcc
                    msg.attach(MIMEText(self.props.body or "", self.props.body_type))
                    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
                    r = await client.post(f"{GMAIL_API}/users/me/messages/send", headers=headers, json={"raw": raw})
                    r.raise_for_status(); return NodeResult(success=True, output_data=r.json())
                elif op == "search":
                    params = {"q": self.props.query or "", "maxResults": min(self.props.max_results, 500)}
                    r = await client.get(f"{GMAIL_API}/users/me/messages", headers=headers, params=params)
                    r.raise_for_status(); data = r.json()
                    return NodeResult(success=True, output_data={"messages": data.get("messages", []), "count": data.get("resultSizeEstimate", 0)})
                elif op == "get_email":
                    if not self.props.message_id: return NodeResult(success=False, error="message_id required")
                    r = await client.get(f"{GMAIL_API}/users/me/messages/{self.props.message_id}", headers=headers)
                    r.raise_for_status(); return NodeResult(success=True, output_data=r.json())
                elif op == "list_labels":
                    r = await client.get(f"{GMAIL_API}/users/me/labels", headers=headers)
                    r.raise_for_status(); return NodeResult(success=True, output_data={"labels": r.json().get("labels", [])})
                elif op == "get_profile":
                    r = await client.get(f"{GMAIL_API}/users/me/profile", headers=headers)
                    r.raise_for_status(); return NodeResult(success=True, output_data=r.json())
                else:
                    return NodeResult(success=False, error=f"Unknown operation: {op}")
        except httpx.HTTPStatusError as e:
            return NodeResult(success=False, error=f"Gmail API error {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            logger.error(f"GmailNode failed: {e}", exc_info=True); return NodeResult(success=False, error=str(e))
