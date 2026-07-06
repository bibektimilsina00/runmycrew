"""add crew and crew_execution tables

Revision ID: f2a9c4d17e6b
Revises: a3f7c1e40b92
Create Date: 2026-07-07 09:00:00.000000

Introduces the standalone `crew` entity (a first-class model, no longer
piggybacking on the `kind=loop` workflow hack) plus its own run-history
table `crew_execution`. Stage 1 foundation only — no execution engine
yet. Both tables cascade on workspace/crew delete so removing an account
or a crew doesn't leave orphans.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from apps.api.app.shared.sqlmodel import UTCDateTime

revision = "f2a9c4d17e6b"
down_revision = "a3f7c1e40b92"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "crew",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "graph",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text('\'{"nodes": [], "edges": []}\'::json'),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("color", sa.String(length=50), nullable=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
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
    )
    op.create_index("ix_crew_user_id", "crew", ["user_id"])
    op.create_index("ix_crew_workspace_id", "crew", ["workspace_id"])

    op.create_table(
        "crew_execution",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "crew_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("crew.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("trigger_type", sa.String(), nullable=False),
        sa.Column("input_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("output_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", UTCDateTime(), nullable=True),
        sa.Column("finished_at", UTCDateTime(), nullable=True),
        sa.Column("snapshot", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("resume_token", sa.String(), nullable=True),
        sa.Column("resume_schema", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("paused_node_id", sa.String(), nullable=True),
        sa.Column("logs", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("ix_crew_execution_crew_id", "crew_execution", ["crew_id"])


def downgrade() -> None:
    op.drop_table("crew_execution")
    op.drop_table("crew")
