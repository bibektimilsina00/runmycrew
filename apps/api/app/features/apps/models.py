"""Data models backing Publish-as-App.

- ``PublishedApp`` — one row per published workflow, versioned. Snapshots the
  graph at publish time so live edits don't affect a running app.
- ``AppSession`` — one row per anonymous cookie (or logged-in user) visiting
  the app. Tracks cumulative cost + message count for rate-limit and cap.
- ``AppMessage`` — every user + assistant turn in a session, with the
  artifact payload emitted by the workflow run.
- ``AppFile`` — files uploaded by visitors (only when the app allows it).
- ``AppEvent`` — analytics stream for retention + funnels.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Column, Index, text
from sqlmodel import Field, Relationship

from apps.api.app.shared.sqlmodel import (
    SQLModelBase,
    UTCDateTime,
    created_at_field,
    updated_at_field,
)

if TYPE_CHECKING:
    pass


class PublishedApp(SQLModelBase, table=True):
    __tablename__ = "published_app"
    __table_args__ = (
        # Partial unique index: at most one active row per (workspace, slug).
        # Inactive versions may share the slug (that's version history).
        # Must match the DDL in migration ``d7a2c4b18e42``.
        Index(
            "uq_published_app_ws_slug_active",
            "workspace_id",
            "app_slug",
            unique=True,
            postgresql_where=text("is_active"),
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    workflow_id: uuid.UUID = Field(foreign_key="workflow.id", ondelete="CASCADE", index=True)
    published_by: uuid.UUID = Field(foreign_key="user.id")

    app_slug: str = Field(max_length=128, index=True)
    title: str = Field(max_length=255)
    description: str | None = Field(default=None)
    mode: str = Field(default="chat", max_length=32)  # chat | form | agent

    # Version pinning — snapshot of the graph at publish time. Live workflow
    # edits do not touch a running app; user must re-publish to promote.
    graph_snapshot: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False, default=dict)
    )
    version_num: int = Field(default=1)
    previous_version_id: uuid.UUID | None = Field(default=None)

    # Full config JSON — theme, welcome, suggested_prompts, input_fields,
    # rate limits, cost caps, captcha, expiry. Kept as one blob so adding
    # new config knobs doesn't need a migration each time.
    config: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False, default=dict)
    )

    # Auth
    auth_mode: str = Field(default="public", max_length=32)  # public | password | login | api_key
    password_hash: str | None = Field(default=None)
    api_key_hash: str | None = Field(default=None)

    # Lifecycle
    is_active: bool = Field(default=True, index=True)
    published_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()
    expires_at: datetime | None = Field(default=None, sa_column=Column(UTCDateTime()))


class AppSession(SQLModelBase, table=True):
    __tablename__ = "app_session"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    app_id: uuid.UUID = Field(foreign_key="published_app.id", ondelete="CASCADE", index=True)
    cookie_id: str = Field(max_length=64, index=True)  # opaque UUID stored in cookie
    user_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", index=True)
    ip_hash: str | None = Field(default=None, max_length=64)  # sha256

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
    role: str = Field(max_length=16)  # user | assistant | system
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


class AppEvent(SQLModelBase, table=True):
    """Append-only analytics stream. Retention analysis + funnels."""

    __tablename__ = "app_event"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    app_id: uuid.UUID = Field(foreign_key="published_app.id", ondelete="CASCADE", index=True)
    session_id: uuid.UUID | None = Field(
        default=None, foreign_key="app_session.id", ondelete="CASCADE"
    )
    type: str = Field(max_length=64, index=True)
    payload: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False, default=dict)
    )
    at: datetime = created_at_field()
