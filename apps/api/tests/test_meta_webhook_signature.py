"""Smoke tests for the Meta webhook signature verifier.

Signature verification is security-sensitive: a bug here would let any
unauthenticated client trigger workflows on any user's Meta account. The
test exercises the happy path + the three failure modes (bad sig,
missing header, missing secret) so a regression flips CI red.
"""

from __future__ import annotations

import hashlib
import hmac

import pytest

from apps.api.app.core.config import settings
from apps.api.app.features.meta.service import verify_webhook_signature


@pytest.fixture(autouse=True)
def _set_app_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "META_APP_SECRET", "test-app-secret")


def _sign(body: bytes) -> str:
    digest = hmac.new(b"test-app-secret", body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_valid_signature_accepted() -> None:
    body = b'{"object":"instagram","entry":[]}'
    assert verify_webhook_signature(body, _sign(body)) is True


def test_tampered_body_rejected() -> None:
    body = b'{"object":"instagram"}'
    sig = _sign(body)
    tampered = b'{"object":"instagram","entry":[{"id":"bad"}]}'
    assert verify_webhook_signature(tampered, sig) is False


def test_missing_header_rejected() -> None:
    assert verify_webhook_signature(b"{}", None) is False
    assert verify_webhook_signature(b"{}", "") is False


def test_wrong_scheme_rejected() -> None:
    body = b"{}"
    digest = hmac.new(b"test-app-secret", body, hashlib.sha256).hexdigest()
    # Meta only signs with sha256 — sha1 (legacy) must not be accepted.
    assert verify_webhook_signature(body, f"sha1={digest}") is False


def test_missing_app_secret_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "META_APP_SECRET", "")
    body = b"{}"
    assert verify_webhook_signature(body, _sign(body)) is False


def test_malformed_header_rejected() -> None:
    assert verify_webhook_signature(b"{}", "totallybroken") is False
    assert verify_webhook_signature(b"{}", "sha256") is False
