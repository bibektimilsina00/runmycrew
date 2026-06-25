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
#
# Transactional email design notes:
# - Light theme by default — Gmail/Outlook treat dark-themed HTML
#   inconsistently (some strip backgrounds, some auto-invert).
# - Table-based + inline styles only — Outlook ignores most CSS.
# - 600px max width — universal safe width across clients.
# - Preheader text — short hidden line that previews in inbox listings.
# - Bulletproof CTA — solid color, big tap target, fallback URL printed
#   below the button so users can copy/paste when buttons are stripped.

BRAND_ACCENT = "#5e6ad2"  # Linear-style indigo, matches default app theme
BRAND_ACCENT_HOVER = "#4a55c2"
TEXT_PRIMARY = "#0e1116"
TEXT_BODY = "#4a5060"
TEXT_MUTED = "#8b909c"
BORDER = "#e6e8ec"
CARD_BG = "#ffffff"
PAGE_BG = "#f6f7f9"
FONT_STACK = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
# Public PNG of the RunMyCrew brand mark on a transparent background.
# PNG (not SVG) because Gmail and several mobile clients strip <img src>
# pointing at SVG. Transparent variant (vs the solid-black icon-192.png
# used for favicons) so the mark sits on the email card's white surface
# without a black square around it.
BRAND_LOGO_URL = "https://runmycrew.com/icon-192-transparent.png"


def _layout(*, preheader: str, heading: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>{heading}</title>
</head>
<body style="margin:0;padding:0;background:{PAGE_BG};font-family:{FONT_STACK};color:{TEXT_PRIMARY};-webkit-font-smoothing:antialiased">
<!-- Inbox preview text -->
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;font-size:1px;line-height:1px;color:{PAGE_BG};opacity:0">
{preheader}
</div>
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:{PAGE_BG}">
  <tr>
    <td align="center" style="padding:40px 16px">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="600" style="max-width:600px;width:100%">
        <!-- Wordmark -->
        <tr>
          <td style="padding:0 4px 24px">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="vertical-align:middle;line-height:0">
                  <img src="{BRAND_LOGO_URL}" width="28" height="28" alt="RunMyCrew" style="display:block;width:28px;height:28px;border:0">
                </td>
                <td style="padding-left:10px;vertical-align:middle">
                  <span style="font-size:16px;font-weight:600;color:{TEXT_PRIMARY};letter-spacing:-.01em">RunMyCrew</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <!-- Card -->
        <tr>
          <td style="background:{CARD_BG};border:1px solid {BORDER};border-radius:14px;box-shadow:0 1px 2px rgba(15,17,22,.04);padding:40px 40px 36px">
            <h1 style="margin:0 0 20px;font-size:24px;line-height:1.25;font-weight:600;color:{TEXT_PRIMARY};letter-spacing:-.01em">{heading}</h1>
            {body_html}
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="padding:24px 8px 0;text-align:center">
            <p style="margin:0;font-size:12px;line-height:1.6;color:{TEXT_MUTED}">
              Sent by RunMyCrew · <a href="https://runmycrew.com" style="color:{TEXT_MUTED};text-decoration:underline">runmycrew.com</a><br>
              If you weren't expecting this email you can safely ignore it.
            </p>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>"""


def _button(label: str, href: str) -> str:
    return f"""
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:8px 0 24px">
        <tr>
          <td style="border-radius:8px;background:{BRAND_ACCENT}">
            <a href="{href}" style="display:inline-block;padding:13px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;border-radius:8px;background:{BRAND_ACCENT};letter-spacing:-.005em">{label}</a>
          </td>
        </tr>
      </table>"""


def _fallback_url(url: str) -> str:
    return f"""
      <p style="margin:0 0 8px;font-size:13px;color:{TEXT_MUTED}">Or paste this link into your browser:</p>
      <p style="margin:0 0 28px;font-size:13px;line-height:1.5;word-break:break-all">
        <a href="{url}" style="color:{BRAND_ACCENT};text-decoration:underline">{url}</a>
      </p>"""


def _invite_text(e: InviteEmail) -> str:
    return (
        f"You've been invited to {e.workspace_name} on RunMyCrew\n\n"
        f"{e.inviter_email} added you as {e.role}.\n\n"
        f"Accept the invite (expires in 7 days):\n{e.invite_url}\n\n"
        "If you don't have a RunMyCrew account yet you'll be asked to create one.\n"
        "If you weren't expecting this email you can safely ignore it."
    )


def _invite_html(e: InviteEmail) -> str:
    body = f"""
      <p style="margin:0 0 8px;font-size:15px;line-height:1.6;color:{TEXT_BODY}">
        <strong style="color:{TEXT_PRIMARY}">{e.inviter_email}</strong> invited you to join
      </p>
      <p style="margin:0 0 6px;font-size:20px;line-height:1.3;font-weight:600;color:{TEXT_PRIMARY};letter-spacing:-.01em">
        {e.workspace_name}
      </p>
      <p style="margin:0 0 24px;font-size:14px;color:{TEXT_MUTED}">
        Role · <span style="color:{TEXT_PRIMARY};font-weight:500">{e.role}</span>
      </p>
      {_button("Accept invite", e.invite_url)}
      {_fallback_url(e.invite_url)}
      <p style="margin:0;padding:14px 16px;border:1px solid {BORDER};border-radius:8px;background:#fafbfc;font-size:13px;line-height:1.5;color:{TEXT_MUTED}">
        This invite expires in <strong style="color:{TEXT_PRIMARY}">7 days</strong>.
        If you don't have a RunMyCrew account yet you'll be prompted to create one.
      </p>"""
    return _layout(
        preheader=f"{e.inviter_email} invited you to {e.workspace_name} on RunMyCrew",
        heading="You've been invited",
        body_html=body,
    )


def _password_reset_text(e: PasswordResetEmail) -> str:
    return (
        "Reset your RunMyCrew password\n\n"
        "We received a request to reset the password on your RunMyCrew account.\n\n"
        f"Reset your password (expires in {e.expires_minutes} minutes):\n{e.reset_url}\n\n"
        "If you didn't request this you can safely ignore this email — "
        "your password won't change."
    )


def _password_reset_html(e: PasswordResetEmail) -> str:
    body = f"""
      <p style="margin:0 0 24px;font-size:15px;line-height:1.6;color:{TEXT_BODY}">
        We received a request to reset the password on your RunMyCrew account.
        Click the button below to choose a new one.
      </p>
      {_button("Reset password", e.reset_url)}
      {_fallback_url(e.reset_url)}
      <p style="margin:0;padding:14px 16px;border:1px solid {BORDER};border-radius:8px;background:#fafbfc;font-size:13px;line-height:1.5;color:{TEXT_MUTED}">
        This link expires in <strong style="color:{TEXT_PRIMARY}">{e.expires_minutes} minutes</strong>.
        If you didn't request a password reset you can safely ignore this email — your password won't change.
      </p>"""
    return _layout(
        preheader=f"Reset your RunMyCrew password (expires in {e.expires_minutes} minutes)",
        heading="Reset your password",
        body_html=body,
    )
