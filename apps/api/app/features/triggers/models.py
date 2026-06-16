from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field

from apps.api.app.shared.sqlmodel import (
    SQLModelBase,
    UTCDateTime,
    created_at_field,
    updated_at_field,
)


class TriggerFixture(SQLModelBase, table=True):
    """The last payload that successfully fired a workflow's trigger node.

    Captured by every transport that dispatches a trigger (Meta webhook,
    generic webhook, Slack events, future Stripe/GitHub/etc.). Used to:

      - Power "Replay" — manual runs from the editor inject the stored
        payload instead of `{}`, so the user sees real downstream output
        without re-triggering the external event each iteration.
      - Bootstrap node testing right after a workflow is built — once
        any event arrives, the user can iterate on downstream nodes
        offline.

    One row per `(workflow_id, node_id)`. Newer payloads overwrite
    older ones — the canonical "last delivery" is enough; full event
    history lives in the execution log.
    """

    __table_args__ = (
        UniqueConstraint(
            "workflow_id",
            "node_id",
            name="uq_trigger_fixture_workflow_node",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workflow_id: uuid.UUID = Field(foreign_key="workflow.id", ondelete="CASCADE", index=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    node_id: str = Field(max_length=128)

    # The payload the trigger node receives as `input_data`. Matches the
    # shape MetaService._flatten_entry emits for Meta deliveries; other
    # transports stamp their own envelopes the same way.
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    # Free-form transport tag — "meta", "webhook", "slack", … — so the
    # inspector can label where the captured event came from.
    source: str = Field(max_length=64, default="webhook")
    captured_at: datetime = Field(
        default=None,
        sa_column=Column(UTCDateTime(), nullable=False),
    )

    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()


class IntegrationTriggerState(SQLModelBase, table=True):
    """Per-(workflow, node) cursor for polling-based trigger nodes.

    Polling triggers (Gmail / Calendar / Drive / Sheets / Notion search /
    HubSpot timeline / …) need a checkpoint so each poll only surfaces
    *new* items, not every item that has ever existed. We park that
    checkpoint here keyed by the trigger node it belongs to.

    The `cursor` payload shape is provider-specific — Gmail keeps a
    `historyId`, Calendar keeps a `syncToken`, Drive keeps a
    `pageToken`. The trigger node owns the shape; this table just keeps
    bytes safe across polls. `provider` is stamped alongside so the
    background poller can fan out by integration type.

    One row per `(workflow_id, node_id)`. Activation creates the row +
    a fresh snapshot; deactivation/delete cascades drop it so a
    re-enable starts from scratch.
    """

    __table_args__ = (
        UniqueConstraint(
            "workflow_id",
            "node_id",
            name="uq_integration_trigger_state_workflow_node",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workflow_id: uuid.UUID = Field(foreign_key="workflow.id", ondelete="CASCADE", index=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    node_id: str = Field(max_length=128)

    # Short tag so the polling scheduler can group by integration
    # ("gmail", "calendar", "drive", …) and per-tenant rate-limit
    # against the right provider.
    provider: str = Field(max_length=32, index=True)

    # Opaque per-provider cursor — e.g. `{"history_id": "12345"}` for
    # Gmail, `{"sync_token": "…"}` for Calendar. Schema lives with the
    # trigger node implementation, not here.
    cursor: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    # When the scheduler last ran a poll for this row. Used both to
    # surface "last fired" in the editor and to enforce per-node
    # cooldowns when the user has configured a long polling cadence.
    last_polled_at: datetime | None = Field(
        default=None,
        sa_column=Column(UTCDateTime(), nullable=True),
    )
    # When the next poll should happen. The scheduler reads rows where
    # `next_poll_at <= now()` and processes them in id order to avoid
    # double-processing under concurrent workers.
    next_poll_at: datetime | None = Field(
        default=None,
        sa_column=Column(UTCDateTime(), nullable=True, index=True),
    )
    # Last error from the poller (e.g. token revoked, 5xx from Google).
    # Cleared on the next successful poll. Surfaced in the editor so the
    # user knows why their trigger went quiet.
    last_error: str | None = Field(default=None, max_length=1024)

    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()
