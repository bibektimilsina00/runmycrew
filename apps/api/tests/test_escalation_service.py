"""Unit tests for the escalation service."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from apps.api.app.features.escalation.schemas import EscalationConfig, EscalationPayload
from apps.api.app.features.escalation.service import EscalationService


def _payload() -> EscalationPayload:
    now = datetime.now(UTC)
    return EscalationPayload(
        workflow_id=uuid4(),
        workflow_name="Test Loop",
        run_id=uuid4(),
        run_url="https://app.runmycrew.com/runs/abc",
        status="failed",
        failure_reason="linear.update_issue returned 401",
        started_at=now,
        ended_at=now,
        trace_summary="step 1: linear_list\nstep 2: linear_update — error",
        usage={"cost_usd": 0.03, "input_tokens": 1820},
    )


@pytest.fixture
def anyio_backend():
    return "asyncio"


# ── Dispatch routing ───────────────────────────────────────────────


@pytest.mark.anyio
async def test_no_config_is_silent():
    svc = EscalationService()
    result = await svc.dispatch(None, _payload())
    assert result["sent"] is False
    assert result["error"] == "no_config"


@pytest.mark.anyio
async def test_disabled_config_is_silent():
    svc = EscalationService()
    cfg = EscalationConfig(workspace_id=uuid4(), enabled=False, slack_webhook_url="https://x")
    result = await svc.dispatch(cfg, _payload())
    assert result["sent"] is False


@pytest.mark.anyio
async def test_no_channel_configured():
    svc = EscalationService()
    cfg = EscalationConfig(workspace_id=uuid4())
    result = await svc.dispatch(cfg, _payload())
    assert result["sent"] is False
    assert result["error"] == "no_channel_configured"


@pytest.mark.anyio
async def test_slack_dispatch():
    svc = EscalationService()
    cfg = EscalationConfig(
        workspace_id=uuid4(),
        slack_webhook_url="https://hooks.slack.com/services/T/B/X",
    )
    mock_resp = AsyncMock()
    mock_resp.raise_for_status = AsyncMock()
    with patch("httpx.AsyncClient.post", return_value=mock_resp) as post:
        result = await svc.dispatch(cfg, _payload())
    assert result["sent"] is True
    assert result["channel"] == "slack"
    post.assert_called_once()
    body = post.call_args.kwargs["json"]
    assert "blocks" in body
    # Header block first
    assert body["blocks"][0]["type"] == "header"


@pytest.mark.anyio
async def test_webhook_dispatch():
    svc = EscalationService()
    cfg = EscalationConfig(workspace_id=uuid4(), webhook_url="https://example.com/hook")
    mock_resp = AsyncMock()
    mock_resp.raise_for_status = AsyncMock()
    with patch("httpx.AsyncClient.post", return_value=mock_resp) as post:
        result = await svc.dispatch(cfg, _payload())
    assert result["sent"] is True
    assert result["channel"] == "webhook"
    post.assert_called_once()
    # Body should be the full payload as JSON
    body = post.call_args.kwargs["json"]
    assert body["workflow_name"] == "Test Loop"
    assert body["status"] == "failed"


@pytest.mark.anyio
async def test_failure_is_logged_not_raised():
    svc = EscalationService()
    cfg = EscalationConfig(workspace_id=uuid4(), webhook_url="https://example.com/hook")
    with patch("httpx.AsyncClient.post", side_effect=RuntimeError("boom")):
        result = await svc.dispatch(cfg, _payload())
    assert result["sent"] is False
    assert "boom" in result["error"]


# ── Payload builder ────────────────────────────────────────────────


def test_build_payload_from_run_includes_trace_summary():
    svc = EscalationService()
    trace = [
        {"step": 0, "tool_call": {"name": "linear_list", "args": {"queue": "Bug"}}},
        {"step": 1, "tool_call": {"name": "linear_update", "args": {"id": "ENG-1"}}},
    ]
    now = datetime.now(UTC)
    payload = svc.build_payload_from_run(
        workflow_id=uuid4(),
        workflow_name="Triage",
        run_id=uuid4(),
        status="failed",
        failure_reason="rate limit",
        started_at=now,
        ended_at=now,
        trace=trace,
        usage={"cost_usd": 0.01},
    )
    assert payload.last_tool_call == "linear_update"
    assert payload.trace_summary is not None
    assert "linear_list" in payload.trace_summary
    assert "linear_update" in payload.trace_summary


def test_build_payload_handles_empty_trace():
    svc = EscalationService()
    now = datetime.now(UTC)
    payload = svc.build_payload_from_run(
        workflow_id=uuid4(),
        workflow_name="Triage",
        run_id=uuid4(),
        status="budget_exhausted",
        failure_reason="iterations",
        started_at=now,
        ended_at=now,
        trace=None,
        usage=None,
    )
    assert payload.trace_summary is None
    assert payload.last_tool_call is None
    assert payload.usage == {}
