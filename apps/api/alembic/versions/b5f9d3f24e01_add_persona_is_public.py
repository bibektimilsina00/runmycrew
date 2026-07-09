"""add is_public flag to persona

Revision ID: b5f9d3f24e01
Revises: a4f8c2e13d90
Create Date: 2026-07-09 11:30:00.000000

Persona sharing — flip is_public on a persona and it becomes visible in
the public gallery for any workspace to import. Cross-workspace import
copies the row, so downstream edits stay per-workspace.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "b5f9d3f24e01"
down_revision = "a4f8c2e13d90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "persona",
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_persona_is_public", "persona", ["is_public"])


def downgrade() -> None:
    op.drop_index("ix_persona_is_public", table_name="persona")
    op.drop_column("persona", "is_public")
