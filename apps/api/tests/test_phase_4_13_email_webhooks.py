"""Unit tests for Phase 4.13 email-provider webhook triggers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from apps.api.app.features.webhooks.signature_schemes import (
    verify_hmac_sha1_b64,
    verify_mailgun,
)
from apps.api.app.node_system.nodes.loops import (
    loops_webhook as _loops_wh,  # noqa: F401
)
from apps.api.app.node_system.nodes.loops.webhook_manifest import (
    MANIFEST as LOOPS,
)
from apps.api.app.node_system.nodes.loops.webhook_manifest import (
    _shape as loops_shape,
)
from apps.api.app.node_system.nodes.mailgun import (
    mailgun_webhook as _mg_wh,  # noqa: F401
)
from apps.api.app.node_system.nodes.mailgun.webhook_manifest import (
    MANIFEST as MAILGUN,
)
from apps.api.app.node_system.nodes.mailgun.webhook_manifest import (
    _shape as mailgun_shape,
)
from apps.api.app.node_system.nodes.postmark import (
    postmark_webhook as _pm_wh,  # noqa: F401
)
from apps.api.app.node_system.nodes.postmark.webhook_manifest import (
    MANIFEST as POSTMARK,
)
from apps.api.app.node_system.nodes.postmark.webhook_manifest import (
    _shape as postmark_shape,
)

# ── hmac_sha1_b64 scheme ────────────────────────────────────────────


def test_hmac_sha1_b64_accepts_valid_signature() -> None:
    """Postmark's base64 HMAC-SHA1 shape. Guard against a copy-paste
    that swapped the algo to SHA256 (would silently accept invalid
    Postmark deliveries)."""
    body = b'{"RecordType":"Delivery"}'
    secret = "srv_secret"
    digest = hmac.new(secret.encode(), body, hashlib.sha1).digest()
    sig = base64.b64encode(digest).decode()
    assert verify_hmac_sha1_b64(body, secret, sig) is True


def test_hmac_sha1_b64_rejects_hex_form() -> None:
    """If a Postmark customer accidentally configured a hex-form
    signature, we must fail closed — hex and base64 aren't
    interchangeable even for the same underlying digest."""
    body = b'{"RecordType":"Delivery"}'
    secret = "srv_secret"
    hex_sig = hmac.new(secret.encode(), body, hashlib.sha1).hexdigest()
    assert verify_hmac_sha1_b64(body, secret, hex_sig) is False


# ── mailgun body-based scheme ───────────────────────────────────────


def test_mailgun_verifier_reads_signature_from_body() -> None:
    """Mailgun puts the signature inside the JSON body, not a header.
    Verifier must hash `{timestamp}{token}` under the API key and
    compare against `signature.signature`."""
    api_key = "key-abc123"
    ts = str(int(time.time()))
    token = "some-nonce-token"
    expected = hmac.new(api_key.encode(), f"{ts}{token}".encode(), hashlib.sha256).hexdigest()
    body = json.dumps(
        {
            "signature": {"timestamp": ts, "token": token, "signature": expected},
            "event-data": {"event": "delivered"},
        }
    ).encode()
    # header_value is ignored by mailgun verifier — receiver passes "" for
    # header-less providers.
    assert verify_mailgun(body, api_key, "") is True


def test_mailgun_rejects_stale_timestamp() -> None:
    """5-minute anti-replay tolerance. A captured signed delivery
    can't be replayed a day later."""
    api_key = "key-abc123"
    ts = str(int(time.time()) - 60 * 60)  # 1 hour ago
    token = "some-nonce"
    sig = hmac.new(api_key.encode(), f"{ts}{token}".encode(), hashlib.sha256).hexdigest()
    body = json.dumps({"signature": {"timestamp": ts, "token": token, "signature": sig}}).encode()
    assert verify_mailgun(body, api_key, "") is False


def test_mailgun_rejects_missing_signature_block() -> None:
    """No signature.signature field → fail closed. Guards against
    accidentally treating an unsigned test delivery as valid."""
    body = json.dumps({"event-data": {"event": "delivered"}}).encode()
    assert verify_mailgun(body, "key", "") is False


def test_mailgun_rejects_malformed_json() -> None:
    """Non-JSON body → fail closed. No verifier should trust a body
    it couldn't parse."""
    assert verify_mailgun(b"not json", "key", "") is False


# ── Postmark payload_shape ─────────────────────────────────────────


def test_postmark_shape_hoists_record_type_and_bounce_context() -> None:
    body = {
        "RecordType": "Bounce",
        "MessageID": "abc-123",
        "Recipient": "user@x.io",
        "Email": "user@x.io",
        "Type": "HardBounce",
        "Description": "Mailbox does not exist",
        "ServerID": 42,
        "MessageStream": "outbound",
    }
    out = postmark_shape(body, "Bounce", "d1")
    assert out["event"] == "Bounce"
    assert out["message_id"] == "abc-123"
    assert out["recipient"] == "user@x.io"
    assert out["bounce_type"] == "HardBounce"
    assert out["bounce_description"] == "Mailbox does not exist"


def test_postmark_shape_pulls_click_link() -> None:
    body = {
        "RecordType": "Click",
        "MessageID": "abc",
        "Recipient": "u@x.io",
        "OriginalLink": "https://example.com/target",
        "Client": {"Name": "Chrome"},
    }
    out = postmark_shape(body, "Click", "d")
    assert out["click_link"] == "https://example.com/target"
    assert out["user_agent"] == "Chrome"


# ── Loops payload_shape ────────────────────────────────────────────


def test_loops_shape_hoists_contact_and_campaign() -> None:
    body = {
        "event": "email_opened",
        "email": "u@x.io",
        "contactId": "cont-1",
        "campaignId": "camp-1",
        "campaignName": "Welcome",
        "urlClicked": None,
        "sentAt": "2026-07-04T12:00:00Z",
    }
    out = loops_shape(body, "email_opened", "d")
    assert out["email"] == "u@x.io"
    assert out["contact_id"] == "cont-1"
    assert out["campaign_name"] == "Welcome"


# ── Mailgun payload_shape ──────────────────────────────────────────


def test_mailgun_shape_walks_event_data_envelope() -> None:
    body = {
        "signature": {"timestamp": "1720000000", "token": "t", "signature": "s"},
        "event-data": {
            "event": "delivered",
            "id": "evt-1",
            "timestamp": 1720000000,
            "recipient": "user@x.io",
            "recipient-domain": "x.io",
            "message": {
                "headers": {
                    "message-id": "<msg1@mailgun.org>",
                    "subject": "Hello",
                    "from": "sender@x.io",
                    "to": "user@x.io",
                }
            },
            "delivery-status": {"code": 250, "message": "OK"},
        },
    }
    out = mailgun_shape(body, "delivered", "evt-1")
    assert out["event"] == "delivered"
    assert out["recipient"] == "user@x.io"
    assert out["message_id"] == "<msg1@mailgun.org>"
    assert out["subject"] == "Hello"
    assert out["delivery_code"] == 250


def test_mailgun_shape_click_event_carries_url() -> None:
    body = {
        "event-data": {
            "event": "clicked",
            "recipient": "u@x.io",
            "url": "https://example.com/target",
        }
    }
    out = mailgun_shape(body, "clicked", "d")
    assert out["url"] == "https://example.com/target"


# ── Manifest wiring ────────────────────────────────────────────────


def test_postmark_manifest_covers_sim_event_set() -> None:
    values = {e.value for e in POSTMARK.events}
    assert {
        "Delivery",
        "Bounce",
        "Open",
        "Click",
        "SpamComplaint",
        "SubscriptionChange",
        "ManualSuppression",
    } <= values


def test_loops_manifest_wiring() -> None:
    assert LOOPS.signature.scheme == "hmac_sha256"
    assert LOOPS.event_body_path == "event"


def test_mailgun_manifest_uses_body_based_scheme() -> None:
    """Mailgun's signature scheme + empty header_name are the load-
    bearing wiring — regression here silently accepts every delivery."""
    assert MAILGUN.signature.scheme == "mailgun"
    assert MAILGUN.signature.header_name == ""
    assert MAILGUN.event_body_path == "event-data.event"
