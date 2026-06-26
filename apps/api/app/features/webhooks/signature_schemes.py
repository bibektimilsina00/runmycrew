"""Signature-verification primitives for the webhook scaffold.

Each provider declares a `SignatureScheme` on its manifest; the
receiver looks the scheme up here and runs the verify against the raw
request body. Every verifier signature is identical so the receiver
stays scheme-agnostic:

    verify(raw_body: bytes, secret: str, header_value: str,
           timestamp_header: str | None) -> bool

Two of the schemes (Stripe, Shopify) have provider-specific quirks —
Stripe interleaves a timestamp into the signed payload to defeat
replay; Shopify base64-encodes the digest. Keep their logic isolated
here so the receiver can stay one if-tree.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time

from apps.api.app.node_system.scaffolds.webhook_manifest import SignatureScheme


def _hmac_hex(secret: str, body: bytes, algo: str = "sha256") -> str:
    return hmac.new(secret.encode("utf-8"), body, getattr(hashlib, algo)).hexdigest()


def _strip_prefix(value: str, prefix: str) -> str:
    return value[len(prefix) :] if prefix and value.startswith(prefix) else value


def verify_hmac_sha256(
    raw_body: bytes,
    secret: str,
    header_value: str,
    *,
    prefix: str = "sha256=",
    timestamp_header: str | None = None,  # noqa: ARG001 — scheme is timestamp-free
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
    timestamp_header: str | None = None,  # noqa: ARG001
) -> bool:
    """Legacy GitHub `X-Hub-Signature` (no `-256`). Useful for providers
    still on the older v1 webhook header."""
    if not secret or not header_value:
        return False
    received = _strip_prefix(header_value, prefix)
    expected = _hmac_hex(secret, raw_body, "sha1")
    return hmac.compare_digest(received, expected)


def verify_stripe(
    raw_body: bytes,
    secret: str,
    header_value: str,
    *,
    prefix: str = "",  # noqa: ARG001 — Stripe header is structured, not prefixed
    timestamp_header: str | None = None,  # noqa: ARG001 — embedded in the header
    tolerance_seconds: int = 60 * 5,
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
    timestamp_header: str | None = None,  # noqa: ARG001
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
    timestamp_header: str | None = None,  # noqa: ARG001
) -> bool:
    """GitLab ships the secret itself in `X-Gitlab-Token`. We compare
    directly under `compare_digest` to defeat timing leaks even though
    no hash is involved.

    Promoting bare-secret compare into a first-class scheme makes it
    available to any future provider with the same shape (Asana, Notion
    when they use a bare verification token, …)."""
    if not secret or not header_value:
        return False
    return hmac.compare_digest(header_value, secret)


def verify_none(
    raw_body: bytes,  # noqa: ARG001
    secret: str,  # noqa: ARG001
    header_value: str,  # noqa: ARG001
    *,
    prefix: str = "",  # noqa: ARG001
    timestamp_header: str | None = None,  # noqa: ARG001
) -> bool:
    """No-op verifier. Use only when the provider does its own pre-body
    handshake (e.g. Slack URL-verification path) — manifests should set
    `require_secret=False` alongside this to skip the secret check."""
    return True


_VERIFIERS: dict[SignatureScheme, object] = {
    "hmac_sha256": verify_hmac_sha256,
    "hmac_sha1": verify_hmac_sha1,
    "stripe": verify_stripe,
    "shopify": verify_shopify,
    "gitlab_token": verify_gitlab_token,
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
    "verify_none",
    "verify_shopify",
    "verify_stripe",
]
