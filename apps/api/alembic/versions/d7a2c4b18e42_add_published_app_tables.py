"""add published_app, app_session, app_message, app_file, app_event

Revision ID: d7a2c4b18e42
Revises: c6f2a5b39d10
Create Date: 2026-07-09 13:00:00.000000

Publish-as-App backing tables.

- ``published_app`` — one row per published workflow, versioned. Snapshots
  the graph at publish time so live edits don't affect the running app.
- ``app_session`` — visitor thread (anon cookie or logged-in user).
- ``app_message`` — per-turn message + artifact payload.
- ``app_file`` — visitor uploads (allowed apps only).
- ``app_event`` — append-only analytics stream.

All rows cascade on workspace / app / session delete so removing a
publish tears down its history cleanly.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from apps.api.app.shared.sqlmodel import UTCDateTime

revision = "d7a2c4b18e42"
down_revision = "c6f2a5b39d10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "published_app",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "workflow_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "published_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id"),
            nullable=False,
        ),
        sa.Column("app_slug", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("mode", sa.String(length=32), nullable=False, server_default="chat"),
        sa.Column(
            "graph_snapshot",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
        sa.Column("version_num", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("previous_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "config",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
        sa.Column("auth_mode", sa.String(length=32), nullable=False, server_default="public"),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.Column("api_key_hash", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "published_at",
            UTCDateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            UTCDateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("expires_at", UTCDateTime(), nullable=True),
    )
    # Partial unique index so re-publishing (which deactivates the prior row)
    # can reuse the slug. Multiple inactive versions with the same slug are
    # fine — that's version history.
    op.create_index(
        "uq_published_app_ws_slug_active",
        "published_app",
        ["workspace_id", "app_slug"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )
    op.create_index("ix_published_app_workspace_id", "published_app", ["workspace_id"])
    op.create_index("ix_published_app_workflow_id", "published_app", ["workflow_id"])
    op.create_index("ix_published_app_app_slug", "published_app", ["app_slug"])
    op.create_index("ix_published_app_is_active", "published_app", ["is_active"])

    op.create_table(
        "app_session",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "app_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("published_app.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("cookie_id", sa.String(length=64), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id"),
            nullable=True,
        ),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "first_seen_at",
            UTCDateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "last_seen_at",
            UTCDateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_cost_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_app_session_app_id", "app_session", ["app_id"])
    op.create_index("ix_app_session_cookie_id", "app_session", ["cookie_id"])
    op.create_index("ix_app_session_user_id", "app_session", ["user_id"])
    op.create_index("ix_app_session_is_blocked", "app_session", ["is_blocked"])

    op.create_table(
        "app_message",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("app_session.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.String(), nullable=False, server_default=""),
        sa.Column(
            "artifacts",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
        sa.Column("execution_id", sa.String(length=128), nullable=True),
        sa.Column("tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_error", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            UTCDateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_app_message_session_id", "app_message", ["session_id"])
    op.create_index("ix_app_message_execution_id", "app_message", ["execution_id"])

    op.create_table(
        "app_file",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("app_session.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("mime", sa.String(length=128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            UTCDateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_app_file_session_id", "app_file", ["session_id"])

    op.create_table(
        "app_event",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "app_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("published_app.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("app_session.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
        sa.Column(
            "at",
            UTCDateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_app_event_app_id", "app_event", ["app_id"])
    op.create_index("ix_app_event_type", "app_event", ["type"])


def downgrade() -> None:
    op.drop_table("app_event")
    op.drop_table("app_file")
    op.drop_table("app_message")
    op.drop_table("app_session")
    op.drop_table("published_app")
