"""Unit tests for the shared webhook signature-verification schemes.

Verifiers are security-sensitive — a regression here silently accepts
forged deliveries. Each scheme has a happy-path test plus at least one
tamper case (bad sig / wrong secret / stale timestamp) so CI catches
weakening.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time

from apps.api.app.features.webhooks.signature_schemes import (
    verify_hmac_sha1,
    verify_hmac_sha256,
    verify_hmac_sha256_b64,
    verify_twilio,
    verify_webflow,
)

# ── hmac_sha256 ──────────────────────────────────────────────────────


def test_hmac_sha256_accepts_valid_signature() -> None:
    body = b'{"ok":1}'
    secret = "s3cret"
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_hmac_sha256(body, secret, sig) is True


def test_hmac_sha256_rejects_bad_body() -> None:
    body = b'{"ok":1}'
    secret = "s3cret"
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_hmac_sha256(body + b"x", secret, sig) is False


# ── hmac_sha1 ────────────────────────────────────────────────────────


def test_hmac_sha1_accepts_valid_signature() -> None:
    body = b"{}"
    secret = "s3cret"
    sig = "sha1=" + hmac.new(secret.encode(), body, hashlib.sha1).hexdigest()
    assert verify_hmac_sha1(body, secret, sig) is True


# ── hmac_sha256_b64 (Teams) ──────────────────────────────────────────


def test_hmac_sha256_b64_teams_prefix() -> None:
    """Teams ships `Authorization: HMAC <base64_digest>` with the secret
    itself pre-base64-encoded (Teams generates the token that way)."""
    body = b'{"text":"hi"}'
    key = b"binary-key"
    secret_b64 = base64.b64encode(key).decode()
    digest = base64.b64encode(hmac.new(key, body, hashlib.sha256).digest()).decode()
    assert verify_hmac_sha256_b64(body, secret_b64, f"HMAC {digest}", prefix="HMAC ") is True


def test_hmac_sha256_b64_rejects_wrong_digest() -> None:
    body = b'{"text":"hi"}'
    key = b"binary-key"
    secret_b64 = base64.b64encode(key).decode()
    assert (
        verify_hmac_sha256_b64(body, secret_b64, "HMAC not-a-real-digest", prefix="HMAC ") is False
    )


def test_hmac_sha256_b64_falls_back_when_secret_not_base64() -> None:
    """If the user pastes a raw ascii secret we key on the bytes directly
    rather than 401-ing on a decode failure. Documented behavior — kept
    to keep misconfigured integrations reachable to diagnose."""
    body = b'{"text":"hi"}'
    secret = "raw-ascii-secret-value"  # not base64
    digest = base64.b64encode(hmac.new(secret.encode(), body, hashlib.sha256).digest()).decode()
    assert verify_hmac_sha256_b64(body, secret, digest) is True


# ── twilio ───────────────────────────────────────────────────────────


def _twilio_sign(url: str, form_body: bytes, secret: str) -> str:
    from urllib.parse import parse_qsl

    params = sorted(parse_qsl(form_body.decode("utf-8"), keep_blank_values=True))
    signed = url + "".join(k + v for k, v in params)
    return base64.b64encode(
        hmac.new(secret.encode(), signed.encode(), hashlib.sha1).digest()
    ).decode()


def test_twilio_accepts_valid_signature() -> None:
    url = "https://example.com/api/v1/webhooks/twilio/w/n"
    body = b"From=%2B15551&To=%2B15552&Body=hello"
    secret = "authtoken"
    sig = _twilio_sign(url, body, secret)
    assert verify_twilio(body, secret, sig, url=url) is True


def test_twilio_rejects_url_mismatch() -> None:
    """Twilio signs the exact URL — a reverse-proxy misconfiguration
    that changes the scheme or host must fail loud, not silent-accept."""
    url = "https://example.com/api/v1/webhooks/twilio/w/n"
    body = b"From=%2B15551&Body=hi"
    secret = "authtoken"
    sig = _twilio_sign(url, body, secret)
    assert verify_twilio(body, secret, sig, url="http://different/api") is False


def test_twilio_rejects_body_tamper() -> None:
    url = "https://example.com/api/v1/webhooks/twilio/w/n"
    body = b"From=%2B15551&Body=hi"
    secret = "authtoken"
    sig = _twilio_sign(url, body, secret)
    assert verify_twilio(body + b"&extra=x", secret, sig, url=url) is False


def test_twilio_missing_url_fails_closed() -> None:
    assert verify_twilio(b"", "s", "sig", url=None) is False


# ── webflow ──────────────────────────────────────────────────────────


def _webflow_sign(body: bytes, secret: str, ts_ms: int) -> str:
    signed = f"{ts_ms}:{body.decode()}".encode()
    return hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()


def test_webflow_accepts_valid_signature() -> None:
    body = b'{"triggerType":"form_submission"}'
    secret = "wf_secret"
    ts_ms = int(time.time() * 1000)
    sig = _webflow_sign(body, secret, ts_ms)
    assert verify_webflow(body, secret, sig, headers={"x-webflow-timestamp": str(ts_ms)}) is True


def test_webflow_rejects_stale_timestamp() -> None:
    """5-minute replay window — a delivery older than that is dropped
    even with a valid signature. Prevents captured payloads from being
    replayed."""
    body = b'{"triggerType":"form_submission"}'
    secret = "wf_secret"
    stale_ts = int(time.time() * 1000) - (6 * 60 * 1000)  # 6 minutes ago
    sig = _webflow_sign(body, secret, stale_ts)
    assert (
        verify_webflow(body, secret, sig, headers={"x-webflow-timestamp": str(stale_ts)}) is False
    )


def test_webflow_rejects_missing_timestamp_header() -> None:
    body = b"{}"
    secret = "wf_secret"
    ts_ms = int(time.time() * 1000)
    sig = _webflow_sign(body, secret, ts_ms)
    assert verify_webflow(body, secret, sig, headers={}) is False
