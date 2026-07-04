"""SMTP action node — send email via any SMTP server.

Not a REST scaffold — uses `aiosmtplib` directly. Handles STARTTLS,
implicit SSL (port 465), and plain (dev-only). Credential holds host,
port, username, password, and encryption mode.

The credential is `smtp_credentials` (a plain APIKeyProvider with 5
fields). No OAuth, no bearer — just SMTP auth.
"""

from __future__ import annotations

from email.message import EmailMessage
from typing import Any

import aiosmtplib
from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class SmtpProperties(BaseModel):
    to: str = ""
    cc: str | None = None
    bcc: str | None = None
    subject: str = ""
    body: str = ""
    html: bool = False
    from_address: str | None = None


class SmtpNode(BaseNode[SmtpProperties]):
    @classmethod
    def get_properties_model(cls):
        return SmtpProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.smtp",
            name="SMTP Send",
            category="integration",
            inputs=1,
            outputs=1,
            description="Send email via SMTP (STARTTLS, implicit SSL, or plain).",
            icon="smtp",
            color="#1c1c1c",
            credential_type="smtp_credentials",
            properties=[
                {
                    "name": "to",
                    "label": "To",
                    "type": "string",
                    "required": True,
                    "placeholder": "recipient@example.com, another@example.com",
                },
                {"name": "cc", "label": "CC", "type": "string"},
                {"name": "bcc", "label": "BCC", "type": "string"},
                {"name": "subject", "label": "Subject", "type": "string", "required": True},
                {"name": "body", "label": "Body", "type": "string", "required": True},
                {"name": "html", "label": "Send as HTML", "type": "boolean", "default": False},
                {
                    "name": "from_address",
                    "label": "From (overrides credential)",
                    "type": "string",
                },
            ],
            outputs_schema=[
                {"label": "sent", "type": "boolean"},
                {"label": "message_id", "type": "string"},
                {"label": "recipients", "type": "array"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        cred = self.credential or {}
        host = cred.get("host") or ""
        port = int(cred.get("port") or 587)
        username = cred.get("username") or ""
        password = cred.get("password") or ""
        # `encryption`: starttls (default 587), ssl (implicit, 465), or none.
        encryption = (cred.get("encryption") or "starttls").lower()
        default_from = cred.get("from_address") or username

        if not host:
            return NodeResult(
                success=False,
                error=f"SMTP credential missing host (node {self.node_id})",
            )

        p = self.props
        from_addr = p.from_address or default_from

        def _split(s: str | None) -> list[str]:
            return [x.strip() for x in (s or "").split(",") if x.strip()]

        msg = EmailMessage()
        msg["From"] = from_addr
        msg["Subject"] = p.subject or ""
        msg["To"] = ", ".join(_split(p.to))
        if p.cc:
            msg["Cc"] = ", ".join(_split(p.cc))
        recipients = _split(p.to) + _split(p.cc) + _split(p.bcc)

        if p.html:
            msg.set_content(p.body or "", subtype="html")
        else:
            msg.set_content(p.body or "")

        try:
            smtp = aiosmtplib.SMTP(
                hostname=host,
                port=port,
                use_tls=(encryption == "ssl"),
                start_tls=(encryption == "starttls"),
                timeout=30,
            )
            async with smtp:
                if username and password:
                    await smtp.login(username, password)
                errors, response = await smtp.send_message(msg, recipients=recipients)
        except aiosmtplib.SMTPException as e:
            return NodeResult(success=False, error=f"SMTP send failed: {e}")
        except Exception as e:  # noqa: BLE001
            return NodeResult(success=False, error=f"SMTP send failed: {e}")

        return NodeResult(
            success=True,
            output_data={
                "sent": True,
                "message_id": msg.get("Message-ID", ""),
                "recipients": recipients,
                "errors": errors or {},
                "response": response,
            },
        )
