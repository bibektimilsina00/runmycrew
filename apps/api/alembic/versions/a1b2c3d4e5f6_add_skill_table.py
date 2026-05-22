"""add skill table

Revision ID: a1b2c3d4e5f6
Revises: 7d4c8f91a2b3
Create Date: 2026-05-19 00:00:00.000000

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "a1b2c3d4e5f6"
down_revision = "7d4c8f91a2b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skill",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("description", sa.String(1024), nullable=False, server_default=""),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_skill_user_id", "skill", ["user_id"])
    op.create_unique_constraint("uq_skill_user_name", "skill", ["user_id", "name"])


def downgrade() -> None:
    op.drop_constraint("uq_skill_user_name", "skill", type_="unique")
    op.drop_index("ix_skill_user_id", table_name="skill")
    op.drop_table("skill")
