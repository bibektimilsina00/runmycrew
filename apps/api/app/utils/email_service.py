from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Protocol

import httpx

from apps.api.app.core.config import settings
from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)

# SMTP socket timeout. Without this, smtplib.SMTP() can hang forever
# when outbound ports are blocked (e.g. DigitalOcean droplets block
# 25/465/587 by default), pinning the request thread indefinitely.
SMTP_TIMEOUT_SECONDS = 10

# Resend HTTP API timeout. The API is fast (~200ms) so a tight cap is fine.
RESEND_HTTP_TIMEOUT_SECONDS = 10
RESEND_API_URL = "https://api.resend.com/emails"


@dataclass(frozen=True)
class InviteEmail:
    to_email: str
    workspace_name: str
    inviter_email: str
    invite_url: str
    role: str


@dataclass(frozen=True)
class PasswordResetEmail:
    to_email: str
    reset_url: str
    expires_minutes: int


class EmailProvider(Protocol):
    async def send_workspace_invite(self, email: InviteEmail) -> None: ...
    async def send_password_reset(self, email: PasswordResetEmail) -> None: ...


# ── Dev provider — logs only, no real email ───────────────────────────────────


class DevEmailProvider:
    async def send_workspace_invite(self, email: InviteEmail) -> None:
        logger.info(
            "[DEV EMAIL] Workspace invite to %s for workspace '%s' as %s — URL: %s",
            email.to_email,
            email.workspace_name,
            email.role,
            email.invite_url,
        )

    async def send_password_reset(self, email: PasswordResetEmail) -> None:
        logger.info(
            "[DEV EMAIL] Password reset for %s (expires in %dm) — URL: %s",
            email.to_email,
            email.expires_minutes,
            email.reset_url,
        )


# ── Resend HTTP API provider — preferred (port 443, no SMTP block risk) ──────


class ResendEmailProvider:
    def __init__(self) -> None:
        self.api_key = settings.RESEND_API_KEY
        self.from_addr = settings.SMTP_FROM
        self.from_name = settings.SMTP_FROM_NAME

    async def send_workspace_invite(self, email: InviteEmail) -> None:
        await self._send(
            to=email.to_email,
            subject=f"You've been invited to {email.workspace_name} on RunMyCrew",
            html=_invite_html(email),
            text=_invite_text(email),
        )

    async def send_password_reset(self, email: PasswordResetEmail) -> None:
        await self._send(
            to=email.to_email,
            subject="Reset your RunMyCrew password",
            html=_password_reset_html(email),
            text=_password_reset_text(email),
        )

    async def _send(self, to: str, subject: str, html: str, text: str) -> None:
        async with httpx.AsyncClient(timeout=RESEND_HTTP_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": f"{self.from_name} <{self.from_addr}>",
                    "to": [to],
                    "subject": subject,
                    "html": html,
                    "text": text,
                },
            )
            resp.raise_for_status()
            logger.info("Email sent (resend) → %s: %s", to, subject)


# ── SMTP provider — fallback for self-hosters not using Resend ───────────────


class SmtpEmailProvider:
    def __init__(self) -> None:
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_addr = settings.SMTP_FROM
        self.from_name = settings.SMTP_FROM_NAME
        self.use_tls = settings.SMTP_TLS

    async def send_workspace_invite(self, email: InviteEmail) -> None:
        subject = f"You've been invited to {email.workspace_name} on RunMyCrew"
        await self._send(
            to=email.to_email,
            subject=subject,
            html=_invite_html(email),
            text=_invite_text(email),
        )

    async def send_password_reset(self, email: PasswordResetEmail) -> None:
        subject = "Reset your RunMyCrew password"
        await self._send(
            to=email.to_email,
            subject=subject,
            html=_password_reset_html(email),
            text=_password_reset_text(email),
        )

    async def _send(self, to: str, subject: str, html: str, text: str) -> None:
        import asyncio

        def _blocking_send() -> None:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_addr}>"
            msg["To"] = to
            msg.attach(MIMEText(text, "plain"))
            msg.attach(MIMEText(html, "html"))

            if self.use_tls:
                smtp = smtplib.SMTP(self.host, self.port, timeout=SMTP_TIMEOUT_SECONDS)
            else:
                smtp = smtplib.SMTP_SSL(self.host, self.port, timeout=SMTP_TIMEOUT_SECONDS)
            with smtp:
                if self.use_tls:
                    smtp.starttls()
                if self.user and self.password:
                    smtp.login(self.user, self.password)
                smtp.sendmail(self.from_addr, [to], msg.as_string())
            logger.info("Email sent (smtp) → %s: %s", to, subject)

        # Run blocking SMTP call in a thread so the event loop is not blocked
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _blocking_send)


# ── Service facade (auto-selects provider based on config) ───────────────────


class EmailService:
    def __init__(self, provider: EmailProvider | None = None) -> None:
        if provider is not None:
            self._provider = provider
        elif settings.RESEND_API_KEY:
            self._provider = ResendEmailProvider()
            logger.info("EmailService: using Resend HTTP API")
        elif settings.SMTP_HOST:
            self._provider = SmtpEmailProvider()
            logger.info("EmailService: using SMTP (%s:%s)", settings.SMTP_HOST, settings.SMTP_PORT)
        else:
            self._provider = DevEmailProvider()
            logger.info("EmailService: no email provider configured — emails will be logged only")

    async def send_workspace_invite(self, email: InviteEmail) -> None:
        try:
            await self._provider.send_workspace_invite(email)
        except Exception as exc:
            # Never crash the invite flow because of an email failure
            logger.error("Failed to send invite email to %s: %s", email.to_email, exc)

    async def send_password_reset(self, email: PasswordResetEmail) -> None:
        try:
            await self._provider.send_password_reset(email)
        except Exception as exc:
            # Never crash the password-reset flow because of an email failure
            logger.error("Failed to send password-reset email to %s: %s", email.to_email, exc)


# ── Templates ─────────────────────────────────────────────────────────────────


def _invite_text(e: InviteEmail) -> str:
    return (
        f"{e.inviter_email} has invited you to join {e.workspace_name} on RunMyCrew as {e.role}.\n\n"
        f"Accept the invite (expires in 7 days):\n{e.invite_url}\n\n"
        "If you don't have a RunMyCrew account you'll be asked to create one first.\n"
        "If you weren't expecting this email you can safely ignore it."
    )


def _invite_html(e: InviteEmail) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f0f0f;color:#fff;margin:0;padding:40px 20px">
  <div style="max-width:520px;margin:0 auto;background:#1a1a1a;border-radius:12px;border:1px solid #2a2a2a;overflow:hidden">
    <div style="padding:32px 32px 24px;border-bottom:1px solid #2a2a2a">
      <p style="font-size:13px;color:#666;margin:0 0 8px;letter-spacing:.05em;text-transform:uppercase">RunMyCrew</p>
      <h1 style="font-size:22px;font-weight:700;margin:0;color:#fff">You're invited</h1>
    </div>
    <div style="padding:32px">
      <p style="color:#aaa;line-height:1.6;margin:0 0 8px">
        <strong style="color:#fff">{e.inviter_email}</strong> has invited you to join
      </p>
      <p style="font-size:20px;font-weight:700;color:#fff;margin:0 0 24px">{e.workspace_name}</p>
      <p style="color:#888;font-size:13px;margin:0 0 28px">
        You'll join as <span style="color:#fff;font-weight:600">{e.role}</span>.
      </p>
      <a href="{e.invite_url}"
         style="display:inline-block;background:#fff;color:#000;font-weight:600;font-size:14px;
                padding:13px 32px;border-radius:8px;text-decoration:none;letter-spacing:.01em">
        Accept Invite →
      </a>
      <p style="color:#444;font-size:12px;margin:28px 0 0;line-height:1.6">
        This invite expires in 7 days.<br>
        If you don't have a RunMyCrew account you'll be prompted to create one.<br>
        If you weren't expecting this you can safely ignore it.
      </p>
    </div>
  </div>
</body>
</html>"""


def _password_reset_text(e: PasswordResetEmail) -> str:
    return (
        "You requested a password reset for your RunMyCrew account.\n\n"
        f"Reset your password (expires in {e.expires_minutes} minutes):\n{e.reset_url}\n\n"
        "If you didn't request this you can safely ignore this email — your password won't change."
    )


def _password_reset_html(e: PasswordResetEmail) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f0f0f;color:#fff;margin:0;padding:40px 20px">
  <div style="max-width:520px;margin:0 auto;background:#1a1a1a;border-radius:12px;border:1px solid #2a2a2a;overflow:hidden">
    <div style="padding:32px 32px 24px;border-bottom:1px solid #2a2a2a">
      <p style="font-size:13px;color:#666;margin:0 0 8px;letter-spacing:.05em;text-transform:uppercase">RunMyCrew</p>
      <h1 style="font-size:22px;font-weight:700;margin:0;color:#fff">Reset your password</h1>
    </div>
    <div style="padding:32px">
      <p style="color:#aaa;line-height:1.6;margin:0 0 24px">
        You requested a password reset for your RunMyCrew account. Click below to set a new password.
      </p>
      <a href="{e.reset_url}"
         style="display:inline-block;background:#fff;color:#000;font-weight:600;font-size:14px;
                padding:13px 32px;border-radius:8px;text-decoration:none;letter-spacing:.01em">
        Reset Password →
      </a>
      <p style="color:#444;font-size:12px;margin:28px 0 0;line-height:1.6">
        This link expires in {e.expires_minutes} minutes.<br>
        If you didn't request this you can safely ignore this email — your password won't change.
      </p>
    </div>
  </div>
</body>
</html>"""
