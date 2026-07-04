"""Signature-verification primitives for the webhook scaffold.

Each provider declares a `SignatureScheme` on its manifest; the
receiver looks the scheme up here and runs the verify against the raw
request body. Every verifier signature is identical so the receiver
stays scheme-agnostic:

    verify(raw_body: bytes, secret: str, header_value: str,
           *, prefix: str, headers: dict[str, str] | None,
           url: str | None) -> bool

Some schemes need context beyond `(body, secret, header)` — Twilio
signs the URL + form params, Webflow signs a timestamp-prefixed body,
Teams strips a header prefix. The `headers` and `url` kwargs give the
receiver a place to thread that context through without shattering the
uniform signature.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
from urllib.parse import parse_qsl

from apps.api.app.node_system.scaffolds.webhook_manifest import SignatureScheme


def _hmac_hex(secret: str, body: bytes, algo: str = "sha256") -> str:
    return hmac.new(secret.encode("utf-8"), body, getattr(hashlib, algo)).hexdigest()


def _hmac_b64(secret: str, body: bytes, algo: str = "sha256") -> str:
    return base64.b64encode(
        hmac.new(secret.encode("utf-8"), body, getattr(hashlib, algo)).digest()
    ).decode()


def _strip_prefix(value: str, prefix: str) -> str:
    return value[len(prefix) :] if prefix and value.startswith(prefix) else value


def _lookup_header(headers: dict[str, str] | None, name: str) -> str:
    if not headers or not name:
        return ""
    target = name.lower()
    for k, v in headers.items():
        if k.lower() == target:
            return str(v)
    return ""


def verify_hmac_sha256(
    raw_body: bytes,
    secret: str,
    header_value: str,
    *,
    prefix: str = "sha256=",
    headers: dict[str, str] | None = None,  # noqa: ARG001
    url: str | None = None,  # noqa: ARG001
) -> bool:
    """GitHub-style HMAC-SHA256 over the raw body. Used by GitHub,
    GitLab, generic providers that follow the GitHub convention."""
    if not secret or not header_value:
        return False
    received = _strip_prefix(header_value, prefix)
    expected = _hmac_hex(secret, raw_body, "sha256")
    return hmac.compare_digest(received, expected)


def verify_hmac_sha1(
    raw_body: bytes,
    secret: str,
    header_value: str,
    *,
    prefix: str = "sha1=",
    headers: dict[str, str] | None = None,  # noqa: ARG001
    url: str | None = None,  # noqa: ARG001
) -> bool:
    """Legacy GitHub `X-Hub-Signature` (no `-256`). Useful for providers
    still on the older v1 webhook header — including Fireflies."""
    if not secret or not header_value:
        return False
    received = _strip_prefix(header_value, prefix)
    expected = _hmac_hex(secret, raw_body, "sha1")
    return hmac.compare_digest(received, expected)


def verify_hmac_sha256_b64(
    raw_body: bytes,
    secret: str,
    header_value: str,
    *,
    prefix: str = "",
    headers: dict[str, str] | None = None,  # noqa: ARG001
    url: str | None = None,  # noqa: ARG001
) -> bool:
    """HMAC-SHA256 base64. Used by Microsoft Teams outgoing webhooks
    (`Authorization: HMAC {digest}`) and other providers that base64-
    encode a sha256 digest with an optional prefix like `HMAC `."""
    if not secret or not header_value:
        return False
    received = _strip_prefix(header_value, prefix)
    try:
        key = base64.b64decode(secret)
    except Exception:  # noqa: BLE001
        # Teams webhook secrets are already base64; if the user pasted
        # the raw bytes accidentally, fall back to key=secret so we
        # don't hard-fail a misconfiguration into an opaque 401.
        key = secret.encode("utf-8")
    expected = base64.b64encode(hmac.new(key, raw_body, hashlib.sha256).digest()).decode()
    return hmac.compare_digest(received, expected)


def verify_stripe(
    raw_body: bytes,
    secret: str,
    header_value: str,
    *,
    prefix: str = "",  # noqa: ARG001 — Stripe header is structured, not prefixed
    tolerance_seconds: int = 60 * 5,
    headers: dict[str, str] | None = None,  # noqa: ARG001
    url: str | None = None,  # noqa: ARG001
) -> bool:
    """Stripe's `Stripe-Signature` header.

    Format: `t=<unix>,v1=<sig>,v0=<sig>`. We HMAC `{timestamp}.{body}`
    under `v1` and reject deliveries older than the tolerance window
    to defeat replay. See https://stripe.com/docs/webhooks/signatures.
    """
    if not secret or not header_value:
        return False
    parts: dict[str, str] = {}
    for chunk in header_value.split(","):
        chunk = chunk.strip()
        if "=" not in chunk:
            return False  # malformed — bail rather than guess
        key, value = chunk.split("=", 1)
        parts[key] = value
    timestamp = parts.get("t")
    signature = parts.get("v1")
    if not timestamp or not signature:
        return False
    try:
        delta = abs(int(time.time()) - int(timestamp))
    except ValueError:
        return False
    if delta > tolerance_seconds:
        return False
    signed = f"{timestamp}.{raw_body.decode('utf-8', errors='replace')}".encode()
    expected = _hmac_hex(secret, signed, "sha256")
    return hmac.compare_digest(signature, expected)


def verify_shopify(
    raw_body: bytes,
    secret: str,
    header_value: str,
    *,
    prefix: str = "",  # noqa: ARG001 — Shopify ships a bare base64 digest
    headers: dict[str, str] | None = None,  # noqa: ARG001
    url: str | None = None,  # noqa: ARG001
) -> bool:
    """Shopify ships `X-Shopify-Hmac-Sha256` as a *base64* digest, not
    hex like GitHub. Same HMAC-SHA256 secret, different encoding."""
    if not secret or not header_value:
        return False
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(header_value, expected)


def verify_gitlab_token(
    raw_body: bytes,  # noqa: ARG001 — GitLab doesn't HMAC the body
    secret: str,
    header_value: str,
    *,
    prefix: str = "",  # noqa: ARG001
    headers: dict[str, str] | None = None,  # noqa: ARG001
    url: str | None = None,  # noqa: ARG001
) -> bool:
    """GitLab ships the secret itself in `X-Gitlab-Token`. We compare
    directly under `compare_digest` to defeat timing leaks even though
    no hash is involved.

    Promoting bare-secret compare into a first-class scheme makes it
    available to any future provider with the same shape (Fathom's
    `x-webhook-secret`, Azure DevOps Basic-Auth, …)."""
    if not secret or not header_value:
        return False
    return hmac.compare_digest(header_value, secret)


def verify_twilio(
    raw_body: bytes,
    secret: str,
    header_value: str,
    *,
    prefix: str = "",  # noqa: ARG001 — Twilio signature is a bare base64 digest
    headers: dict[str, str] | None = None,  # noqa: ARG001 — verifier reads URL only
    url: str | None = None,
) -> bool:
    """Twilio's `X-Twilio-Signature`.

    Twilio HMACs `{full_url}{sorted key=value form params concatenated}`
    under SHA-1 with the auth token as key, base64. For JSON deliveries
    the body is empty (Twilio only signs form posts), so we still HMAC
    the URL by itself. See:
    https://www.twilio.com/docs/usage/webhooks/webhooks-security

    The router threads `url` through — Twilio validates against the
    *external* URL the customer configured, so any reverse proxy must
    preserve X-Forwarded-Proto/Host or the digest won't match.
    """
    if not secret or not header_value or not url:
        return False
    signed = url
    # Form-encoded body → sort by key, concatenate `k+v` (no separators).
    if raw_body:
        try:
            params = sorted(parse_qsl(raw_body.decode("utf-8"), keep_blank_values=True))
            signed = url + "".join(k + v for k, v in params)
        except Exception:  # noqa: BLE001
            # Non-form body (rare — Twilio Studio can post JSON). The
            # URL alone still yields a valid signature for these cases.
            signed = url
    expected = base64.b64encode(
        hmac.new(secret.encode("utf-8"), signed.encode("utf-8"), hashlib.sha1).digest()
    ).decode()
    return hmac.compare_digest(header_value, expected)


def verify_webflow(
    raw_body: bytes,
    secret: str,
    header_value: str,
    *,
    prefix: str = "",  # noqa: ARG001 — bare hex digest
    tolerance_seconds: int = 60 * 5,
    headers: dict[str, str] | None = None,
    url: str | None = None,  # noqa: ARG001
) -> bool:
    """Webflow v2 signs `timestamp:body` under HMAC-SHA256 hex.

    Timestamp lives in `x-webflow-timestamp` (unix milliseconds). We
    enforce a 5-minute replay window to match Stripe's practice.
    """
    if not secret or not header_value or not headers:
        return False
    ts_raw = _lookup_header(headers, "x-webflow-timestamp")
    if not ts_raw:
        return False
    try:
        ts_ms = int(ts_raw)
    except ValueError:
        return False
    delta_seconds = abs(int(time.time() * 1000) - ts_ms) / 1000
    if delta_seconds > tolerance_seconds:
        return False
    signed = f"{ts_ms}:{raw_body.decode('utf-8', errors='replace')}".encode()
    expected = _hmac_hex(secret, signed, "sha256")
    return hmac.compare_digest(header_value, expected)


def verify_none(
    raw_body: bytes,  # noqa: ARG001
    secret: str,  # noqa: ARG001
    header_value: str,  # noqa: ARG001
    *,
    prefix: str = "",  # noqa: ARG001
    headers: dict[str, str] | None = None,  # noqa: ARG001
    url: str | None = None,  # noqa: ARG001
) -> bool:
    """No-op verifier. Use only when the provider does its own pre-body
    handshake (e.g. Slack URL-verification path) — manifests should set
    `require_secret=False` alongside this to skip the secret check."""
    return True


_VERIFIERS: dict[SignatureScheme, object] = {
    "hmac_sha256": verify_hmac_sha256,
    "hmac_sha1": verify_hmac_sha1,
    "hmac_sha256_b64": verify_hmac_sha256_b64,
    "stripe": verify_stripe,
    "shopify": verify_shopify,
    "gitlab_token": verify_gitlab_token,
    "twilio": verify_twilio,
    "webflow": verify_webflow,
    "none": verify_none,
}


def get_verifier(scheme: SignatureScheme):
    """Return the verifier callable for the named scheme, or None for an
    unknown scheme (the receiver treats unknown as failure)."""
    return _VERIFIERS.get(scheme)


__all__ = [
    "get_verifier",
    "verify_gitlab_token",
    "verify_hmac_sha1",
    "verify_hmac_sha256",
    "verify_hmac_sha256_b64",
    "verify_none",
    "verify_shopify",
    "verify_stripe",
    "verify_twilio",
    "verify_webflow",
]
