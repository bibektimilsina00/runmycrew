"""add copilot session

Revision ID: a1f2e3d4c5b6
Revises: e4f5a6b7c8d9
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1f2e3d4c5b6"
down_revision: str | None = "e4f5a6b7c8d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "copilotsession",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workflow_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False, server_default="New Chat"),
        sa.Column("messages", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_copilotsession_workflow_user", "copilotsession", ["workflow_id", "user_id"])


def downgrade() -> None:
    op.drop_index("ix_copilotsession_workflow_user", table_name="copilotsession")
    op.drop_table("copilotsession")
