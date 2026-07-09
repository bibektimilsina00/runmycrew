"""add persona table

Revision ID: a4f8c2e13d90
Revises: f2a9c4d17e6b
Create Date: 2026-07-09 09:00:00.000000

Personas — reusable named agents that overlay onto ``action.agent`` nodes.
Each persona is scoped to a workspace (cascades on workspace delete) and
carries the default system prompt, tools, provider/model, temperature, and
loop cap that new Agent nodes prefill with.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from apps.api.app.shared.sqlmodel import UTCDateTime

revision = "a4f8c2e13d90"
down_revision = "f2a9c4d17e6b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "persona",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("system_prompt", sa.String(), nullable=False, server_default=""),
        sa.Column("default_provider", sa.String(length=64), nullable=True),
        sa.Column("default_model", sa.String(length=128), nullable=True),
        sa.Column(
            "tools",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
        sa.Column("color", sa.String(length=50), nullable=True),
        sa.Column("icon_slug", sa.String(length=128), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.3"),
        sa.Column("max_iterations", sa.Integer(), nullable=False, server_default="10"),
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
    op.create_index("ix_persona_workspace_id", "persona", ["workspace_id"])
    op.create_index("ix_persona_user_id", "persona", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_persona_user_id", table_name="persona")
    op.drop_index("ix_persona_workspace_id", table_name="persona")
    op.drop_table("persona")
