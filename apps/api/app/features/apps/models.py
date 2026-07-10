"""Data models backing the hosted-app surface.

Design (post-refactor):

- No ``PublishedApp`` row. The workflow itself is the source of truth —
  its ``trigger.chat_app`` node holds config, its ``is_active`` flag is
  the live/off switch, its graph JSON is what runs. Same model as every
  other trigger (webhook / cron / poll).
- Password + API key hashes live on ``Workflow`` (see migration + the
  ``app_password_hash`` / ``app_api_key_hash`` columns) so they don't
  leak in workflow export.
- Visitor state — sessions, messages, files — hangs off ``workflow_id``.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship

from apps.api.app.shared.sqlmodel import (
    SQLModelBase,
    created_at_field,
    updated_at_field,
)


class AppSession(SQLModelBase, table=True):
    __tablename__ = "app_session"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # A session belongs to exactly one chat-app source: a workflow OR a
    # crew (both can carry a trigger.chat_app node). One of the two is set.
    workflow_id: uuid.UUID | None = Field(
        default=None, foreign_key="workflow.id", ondelete="CASCADE", index=True
    )
    crew_id: uuid.UUID | None = Field(
        default=None, foreign_key="crew.id", ondelete="CASCADE", index=True
    )
    cookie_id: str = Field(max_length=64, index=True)
    user_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", index=True)
    ip_hash: str | None = Field(default=None, max_length=64)

    first_seen_at: datetime = created_at_field()
    last_seen_at: datetime = updated_at_field()

    message_count: int = Field(default=0)
    total_cost_usd: float = Field(default=0.0)
    total_tokens: int = Field(default=0)
    is_blocked: bool = Field(default=False, index=True)

    messages: list["AppMessage"] = Relationship(
        back_populates="session", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class AppMessage(SQLModelBase, table=True):
    __tablename__ = "app_message"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="app_session.id", ondelete="CASCADE", index=True)
    role: str = Field(max_length=16)
    content: str = Field(default="")
    artifacts: list[dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False, default=list)
    )
    execution_id: str | None = Field(default=None, max_length=128, index=True)
    tokens: int = Field(default=0)
    cost_usd: float = Field(default=0.0)
    latency_ms: int = Field(default=0)
    is_error: bool = Field(default=False)
    created_at: datetime = created_at_field()

    session: "AppSession" = Relationship(back_populates="messages")


class AppFile(SQLModelBase, table=True):
    __tablename__ = "app_file"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="app_session.id", ondelete="CASCADE", index=True)
    url: str = Field()
    filename: str = Field(max_length=255)
    mime: str = Field(max_length=128)
    size_bytes: int = Field(default=0)
    sha256: str = Field(max_length=64)
    created_at: datetime = created_at_field()
