"""add execution pause/resume fields

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-19 00:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("execution", sa.Column("snapshot", postgresql.JSONB, nullable=True))
    op.add_column("execution", sa.Column("resume_token", sa.String, nullable=True))
    op.add_column("execution", sa.Column("resume_schema", postgresql.JSONB, nullable=True))
    op.add_column("execution", sa.Column("paused_node_id", sa.String, nullable=True))


def downgrade() -> None:
    op.drop_column("execution", "paused_node_id")
    op.drop_column("execution", "resume_schema")
    op.drop_column("execution", "resume_token")
    op.drop_column("execution", "snapshot")
