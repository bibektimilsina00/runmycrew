"""Pydantic schemas for the escalation handler.

Mirrors the JSON shape Slack / Discord / generic webhook handlers
expect. ``EscalationConfig`` is what the workspace stores;
``EscalationPayload`` is what gets POSTed downstream.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EscalationConfig(BaseModel):
    """Workspace-level escalation configuration.

    Exactly one of ``slack_webhook_url`` / ``email_to`` /
    ``webhook_url`` must be set; the runtime picks whichever is
    populated. Default (no row at all) is silent — the loop just
    records the failure to the run history and exits.
    """

    workspace_id: UUID
    slack_webhook_url: str | None = None
    email_to: str | None = None
    webhook_url: str | None = None
    enabled: bool = True


class EscalationPayload(BaseModel):
    """Structured payload forwarded to the configured handler.

    Stable schema — Slack message formatters + downstream webhook
    consumers depend on these keys. Add new optional keys; never
    rename existing ones.
    """

    workflow_id: UUID
    workflow_name: str
    run_id: UUID
    run_url: str
    status: str  # 'failed' | 'budget_exhausted'
    failure_reason: str | None = None
    started_at: datetime
    ended_at: datetime
    trace_summary: str | None = None
    usage: dict[str, Any] = Field(default_factory=dict)
    # Provenance — humans triaging escalations want to know "which
    # agent" or "which integration" caused this.
    agent_label: str | None = None
    last_tool_call: str | None = None
