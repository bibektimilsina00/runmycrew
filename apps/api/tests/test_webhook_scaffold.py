"""Unit tests for the webhook scaffold.

Two layers:

1. Pure verifier tests — `verify_hmac_sha256`, `verify_hmac_sha1`,
   `verify_stripe`, `verify_shopify`, `verify_none`. Each gets a happy
   path and a tamper-detection check.
2. End-to-end receiver flow via `WebhookService.dispatch` with the
   workflow + execution engine mocked — confirms the provider lookup,
   signature verify, event filter, and dispatch all wire through.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from apps.api.app.features.webhooks.service import WebhookService
from apps.api.app.features.webhooks.signature_schemes import (
    verify_hmac_sha1,
    verify_hmac_sha256,
    verify_none,
    verify_shopify,
    verify_stripe,
)

# ── verifier unit tests ──────────────────────────────────────────────


def test_hmac_sha256_accepts_correct_sig():
    body = b'{"hello":"world"}'
    secret = "super-secret"
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_hmac_sha256(body, secret, f"sha256={expected}") is True


def test_hmac_sha256_rejects_tampered_body():
    body = b'{"hello":"world"}'
    secret = "super-secret"
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_hmac_sha256(b'{"hello":"evil"}', secret, f"sha256={sig}") is False


def test_hmac_sha256_rejects_empty_inputs():
    assert verify_hmac_sha256(b"x", "", "sha256=abc") is False
    assert verify_hmac_sha256(b"x", "s", "") is False


def test_hmac_sha1_accepts_correct_sig():
    body = b"some payload"
    secret = "k"
    sig = hmac.new(secret.encode(), body, hashlib.sha1).hexdigest()
    assert verify_hmac_sha1(body, secret, f"sha1={sig}") is True


def test_stripe_accepts_correct_sig_within_tolerance():
    body = b'{"id":"evt_1"}'
    secret = "whsec_test"
    ts = int(time.time())
    signed = f"{ts}.{body.decode()}".encode()
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    header = f"t={ts},v1={sig}"
    assert verify_stripe(body, secret, header) is True


def test_stripe_rejects_replay_beyond_tolerance():
    body = b'{"id":"evt_1"}'
    secret = "whsec_test"
    ts = int(time.time()) - 60 * 60  # one hour ago
    signed = f"{ts}.{body.decode()}".encode()
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    header = f"t={ts},v1={sig}"
    assert verify_stripe(body, secret, header) is False


def test_stripe_rejects_malformed_header():
    assert verify_stripe(b"x", "s", "garbage") is False
    assert verify_stripe(b"x", "s", "t=abc,v1=def") is False  # bad timestamp


def test_shopify_accepts_base64_digest():
    body = b"payload"
    secret = "k"
    digest = base64.b64encode(hmac.new(secret.encode(), body, hashlib.sha256).digest()).decode()
    assert verify_shopify(body, secret, digest) is True


def test_shopify_rejects_hex_digest():
    """Shopify is base64-only; a hex digest must NOT verify."""
    body = b"payload"
    secret = "k"
    hex_digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_shopify(body, secret, hex_digest) is False


def test_none_always_accepts():
    assert verify_none(b"", "", "") is True


# ── end-to-end receiver flow ─────────────────────────────────────────


def _gitlab_workflow(node_id: str = "gitlab-trigger-1", secret: str = "g_token", event: str = "*"):
    """Fake workflow with one gitlab webhook trigger node."""
    return SimpleNamespace(
        id="00000000-0000-0000-0000-000000000001",
        graph={
            "nodes": [
                {
                    "id": node_id,
                    "type": "trigger.gitlab_webhook",
                    "data": {"properties": {"secret": secret, "event": event}},
                }
            ]
        },
    )


@pytest.fixture
def patched_workflow_repo(monkeypatch):
    """Patch `WorkflowRepository.get_by_id` to return our fake workflow."""
    workflow = _gitlab_workflow()

    async def fake_get(self, wf_id):  # noqa: ARG001
        return workflow

    from apps.api.app.features.workflows.repository import WorkflowRepository

    monkeypatch.setattr(WorkflowRepository, "get_by_id", fake_get)
    return workflow


@pytest.fixture
def patched_engine(monkeypatch):
    """Stub the execution engine — return a fixed execution id."""
    from apps.api.app.execution_engine import engine as engine_module

    monkeypatch.setattr(
        engine_module.execution_engine,
        "trigger_workflow",
        AsyncMock(return_value="exec-123"),
    )


@pytest.mark.anyio
async def test_receiver_dispatches_on_valid_signature(patched_workflow_repo, patched_engine):
    # Import the manifest module to register the gitlab provider.
    import apps.api.app.node_system.nodes.gitlab.gitlab_webhook  # noqa: F401

    body = json.dumps({"object_kind": "push", "project": {"path_with_namespace": "g/p"}}).encode()
    headers = {
        "X-Gitlab-Token": "g_token",
        "X-Gitlab-Event": "Push Hook",
    }

    service = WebhookService(db=None)  # db unused — repo is patched
    result = await service.dispatch(
        provider="gitlab",
        workflow_id="00000000-0000-0000-0000-000000000001",
        node_id="gitlab-trigger-1",
        raw_body=body,
        headers=headers,
    )

    assert result["status"] == "accepted"
    assert result["event"] == "Push Hook"
    assert result["execution_id"] == "exec-123"


@pytest.mark.anyio
async def test_receiver_rejects_unknown_provider(patched_workflow_repo):
    service = WebhookService(db=None)
    with pytest.raises(Exception) as exc_info:
        await service.dispatch(
            provider="bogus",
            workflow_id="00000000-0000-0000-0000-000000000001",
            node_id="x",
            raw_body=b"{}",
            headers={},
        )
    # FastAPI's HTTPException — status 404 on unknown provider.
    assert getattr(exc_info.value, "status_code", None) == 404


@pytest.mark.anyio
async def test_receiver_rejects_invalid_signature(patched_workflow_repo):
    import apps.api.app.node_system.nodes.gitlab.gitlab_webhook  # noqa: F401

    service = WebhookService(db=None)
    with pytest.raises(Exception) as exc_info:
        await service.dispatch(
            provider="gitlab",
            workflow_id="00000000-0000-0000-0000-000000000001",
            node_id="gitlab-trigger-1",
            raw_body=b"{}",
            headers={"X-Gitlab-Token": "wrong_token", "X-Gitlab-Event": "Push Hook"},
        )
    assert getattr(exc_info.value, "status_code", None) == 401


@pytest.mark.anyio
async def test_receiver_drops_filtered_event(monkeypatch, patched_engine):
    import apps.api.app.node_system.nodes.gitlab.gitlab_webhook  # noqa: F401
    from apps.api.app.execution_engine import engine as engine_module
    from apps.api.app.features.workflows.repository import WorkflowRepository

    workflow = _gitlab_workflow(event="Push Hook")  # only want push

    async def fake_get(self, wf_id):  # noqa: ARG001
        return workflow

    monkeypatch.setattr(WorkflowRepository, "get_by_id", fake_get)

    service = WebhookService(db=None)
    result = await service.dispatch(
        provider="gitlab",
        workflow_id="00000000-0000-0000-0000-000000000001",
        node_id="gitlab-trigger-1",
        raw_body=b'{"object_kind":"issue"}',
        headers={"X-Gitlab-Token": "g_token", "X-Gitlab-Event": "Issue Hook"},
    )
    assert result["status"] == "ignored"
    # Engine must NOT have been called when the event was filtered out.
    engine_module.execution_engine.trigger_workflow.assert_not_called()  # type: ignore[attr-defined]


@pytest.mark.anyio
async def test_receiver_404_when_node_id_missing(patched_workflow_repo):
    import apps.api.app.node_system.nodes.gitlab.gitlab_webhook  # noqa: F401

    service = WebhookService(db=None)
    with pytest.raises(Exception) as exc_info:
        await service.dispatch(
            provider="gitlab",
            workflow_id="00000000-0000-0000-0000-000000000001",
            node_id="nope",
            raw_body=b"{}",
            headers={"X-Gitlab-Token": "g_token", "X-Gitlab-Event": "Push Hook"},
        )
    assert getattr(exc_info.value, "status_code", None) == 404


@pytest.mark.anyio
async def test_receiver_payload_shape_applied(patched_workflow_repo, monkeypatch):
    """The gitlab manifest's payload_shape should fold the GitLab body
    into our canonical {repository, sender, ...} shape — execution
    engine sees the shaped dict, not the raw payload."""
    import apps.api.app.node_system.nodes.gitlab.gitlab_webhook  # noqa: F401
    from apps.api.app.execution_engine import engine as engine_module

    captured = {}

    async def capture(**kwargs):
        captured.update(kwargs)
        return "exec-shape"

    monkeypatch.setattr(
        engine_module.execution_engine,
        "trigger_workflow",
        capture,
    )

    body = json.dumps(
        {
            "object_kind": "push",
            "project": {"path_with_namespace": "team/repo"},
            "user": {"username": "alice"},
        }
    ).encode()

    service = WebhookService(db=None)
    await service.dispatch(
        provider="gitlab",
        workflow_id="00000000-0000-0000-0000-000000000001",
        node_id="gitlab-trigger-1",
        raw_body=body,
        headers={"X-Gitlab-Token": "g_token", "X-Gitlab-Event": "Push Hook"},
    )

    shaped = captured["input_data"]
    assert shaped["repository"] == "team/repo"
    assert shaped["sender"] == "alice"
    assert shaped["object_kind"] == "push"
    assert shaped["event"] == "Push Hook"
    assert shaped["body"]["object_kind"] == "push"
