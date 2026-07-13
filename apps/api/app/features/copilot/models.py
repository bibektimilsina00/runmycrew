from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Field

from apps.api.app.shared.sqlmodel import SQLModelBase, created_at_field, updated_at_field


class CopilotSession(SQLModelBase, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    )
    # Exactly one of workflow_id / crew_id is set — the entity this copilot
    # thread is editing. Mirrors AppSession's dual-owner shape so the
    # copilot can build crews as well as workflows.
    workflow_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("workflow.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    crew_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("crew.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    title: str = Field(
        default="New Chat",
        sa_column=Column(String(200), nullable=False, default="New Chat"),
    )
    messages: list[dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()
