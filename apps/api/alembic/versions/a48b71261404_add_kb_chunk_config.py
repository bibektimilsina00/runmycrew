"""add_kb_chunk_config

Revision ID: a48b71261404
Revises: d9a7b3c6e101
Create Date: 2026-05-21 01:52:30.200612
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a48b71261404"
down_revision: str | None = "d9a7b3c6e101"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "knowledgebase",
        sa.Column("chunk_size", sa.Integer(), nullable=False, server_default="1000"),
    )
    op.add_column(
        "knowledgebase",
        sa.Column("chunk_overlap", sa.Integer(), nullable=False, server_default="200"),
    )


def downgrade() -> None:
    op.drop_column("knowledgebase", "chunk_overlap")
    op.drop_column("knowledgebase", "chunk_size")
