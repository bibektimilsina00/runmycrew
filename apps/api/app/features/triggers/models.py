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
