"""IMAP polling trigger — manifest form.

Generic email polling — works with any IMAP server (Gmail, Outlook,
Yahoo, self-hosted Dovecot / Cyrus). No HTTP involved; the paginate_fn
drops down to `imaplib` from stdlib and ignores the httpx client the
scaffold passes in.

Credential holds host + port + username + password + use_ssl. The
password field is expected to be an app-password on 2FA-protected
Gmail / Outlook accounts — plain passwords will be rejected by the
server.

Polling strategy: `known_ids` on the mailbox UID. UIDs are stable
within a folder — moving/deleting a message doesn't renumber the
others (unlike sequence numbers).
"""

from __future__ import annotations

import contextlib
import email
import email.utils
import imaplib
from email.header import decode_header
from typing import Any

import httpx  # noqa: F401 — signature contract from scaffold

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)


def _decode_header_value(value: str) -> str:
    """Decode MIME-encoded email headers (RFC 2047) into unicode."""
    if not value:
        return ""
    parts = decode_header(value)
    out: list[str] = []
    for text, charset in parts:
        if isinstance(text, bytes):
            try:
                out.append(text.decode(charset or "utf-8", errors="replace"))
            except LookupError:
                out.append(text.decode("utf-8", errors="replace"))
        else:
            out.append(text)
    return "".join(out).strip()


def _extract_body(msg: email.message.Message) -> tuple[str, str]:
    """Return (text_body, html_body). Multipart messages carry both;
    single-part messages fill only one. Attachments are dropped."""
    text_body = ""
    html_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disposition = str(part.get("Content-Disposition") or "")
            if "attachment" in disposition.lower():
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            try:
                decoded = payload.decode(charset, errors="replace")
            except LookupError:
                decoded = payload.decode("utf-8", errors="replace")
            if ctype == "text/plain" and not text_body:
                text_body = decoded
            elif ctype == "text/html" and not html_body:
                html_body = decoded
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            try:
                decoded = payload.decode(charset, errors="replace")
            except LookupError:
                decoded = payload.decode("utf-8", errors="replace")
            if msg.get_content_type() == "text/html":
                html_body = decoded
            else:
                text_body = decoded
    return text_body, html_body


def _flatten_mail(item):
    return dict(item) if isinstance(item, dict) else {}


register_flatten("imap.mail", _flatten_mail)


def _bool_from_cred(value: Any) -> bool:
    """Cred field is a string — support the common truthy inputs."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "y", "on", "ssl")
    return bool(value)


async def _walk_imap(
    client: Any,  # noqa: ARG001 — httpx client unused; IMAP is not HTTP
    *,
    manifest,
    event,  # noqa: ARG001 — only one event
    token: str | None,  # noqa: ARG001 — auth lives in credential dict
    props: Any,
) -> list[dict[str, Any]]:
    """Connect + login + SEARCH + FETCH. Runs synchronously inside
    the async paginator — imaplib doesn't ship an async API, and
    polling is infrequent so blocking the worker briefly is fine."""
    cred = getattr(props, "_cred", None) or {}
    host = str(cred.get("host") or "").strip()
    username = str(cred.get("username") or "").strip()
    password = str(cred.get("password") or "")
    if not host or not username or not password:
        return []
    port_raw = str(cred.get("port") or "").strip()
    use_ssl = _bool_from_cred(cred.get("use_ssl"))
    try:
        port = int(port_raw) if port_raw else (993 if use_ssl else 143)
    except ValueError:
        port = 993 if use_ssl else 143

    folder = getattr(props, "folder", None) or "INBOX"
    limit_raw = getattr(props, "max_per_poll", 25) or 25
    try:
        limit = max(1, min(int(limit_raw), 100))
    except (TypeError, ValueError):
        limit = 25

    server: imaplib.IMAP4 | None = None
    try:
        server = imaplib.IMAP4_SSL(host, port) if use_ssl else imaplib.IMAP4(host, port)
        server.login(username, password)
        server.select(folder, readonly=True)
        # SEARCH returns sequence numbers by default; we want UIDs so
        # we survive server-side renumbering. `UID SEARCH ALL` then
        # keep the top `limit` newest ids.
        status, data = server.uid("SEARCH", None, "ALL")
        if status != "OK":
            return []
        uids = (data[0] or b"").split()
        if not uids:
            return []
        uids = uids[-limit:]  # newest first (IMAP returns ascending)
        results: list[dict[str, Any]] = []
        for uid in reversed(uids):
            status, msg_data = server.uid("FETCH", uid, "(RFC822)")
            if status != "OK" or not msg_data:
                continue
            raw_bytes = None
            for part in msg_data:
                if isinstance(part, tuple) and len(part) >= 2 and isinstance(part[1], bytes):
                    raw_bytes = part[1]
                    break
            if raw_bytes is None:
                continue
            msg = email.message_from_bytes(raw_bytes)
            text_body, html_body = _extract_body(msg)
            from_addr = _decode_header_value(msg.get("From") or "")
            from_name, from_email = email.utils.parseaddr(from_addr)
            date_str = msg.get("Date") or ""
            results.append(
                {
                    "id": uid.decode() if isinstance(uid, bytes) else str(uid),
                    "message_id": msg.get("Message-ID") or "",
                    "subject": _decode_header_value(msg.get("Subject") or ""),
                    "from_email": from_email,
                    "from_name": from_name or from_addr,
                    "to": _decode_header_value(msg.get("To") or ""),
                    "cc": _decode_header_value(msg.get("Cc") or ""),
                    "date": date_str,
                    "text_body": text_body[:10_000],  # bound payload size
                    "html_body": html_body[:20_000],
                    "folder": folder,
                }
            )
        return results
    except (imaplib.IMAP4.error, OSError) as exc:
        raise RuntimeError(f"IMAP poll failed: {exc}") from exc
    finally:
        if server is not None:
            with contextlib.suppress(imaplib.IMAP4.error, OSError):
                server.close()  # already closed / never selected: suppress
            with contextlib.suppress(imaplib.IMAP4.error, OSError):
                server.logout()


MANIFEST = PollingTriggerManifest(
    type="trigger.imap",
    name="IMAP Email",
    description=(
        "Poll any IMAP mailbox for new messages. Works with Gmail, Outlook, "
        "Yahoo, or self-hosted email. Use an app-password for accounts with "
        "2FA enabled — plain passwords will be rejected by the server."
    ),
    icon_slug="mail",
    color="#ffffff",
    base_url="",
    credential_type="imap_creds",
    token_field=["password"],
    auth="none",  # IMAP handles its own auth via imaplib.login
    provider="imap",
    default_poll_interval_seconds=120,
    min_poll_interval_seconds=60,
    common_fields=[
        FieldSpec(
            name="folder",
            label="Folder",
            type="string",
            default="INBOX",
            placeholder="INBOX",
        ),
    ],
    events=[
        PollingEvent(
            id="new_mail",
            label="New Mail",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="imap.mail",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "message_id", "type": "string"},
        {"label": "subject", "type": "string"},
        {"label": "from_email", "type": "string"},
        {"label": "from_name", "type": "string"},
        {"label": "to", "type": "string"},
        {"label": "date", "type": "string"},
        {"label": "text_body", "type": "string"},
        {"label": "html_body", "type": "string"},
        {"label": "folder", "type": "string"},
    ],
    paginate_fn=_walk_imap,
)
