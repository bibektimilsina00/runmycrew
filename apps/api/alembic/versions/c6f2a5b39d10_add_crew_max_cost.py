"""add max_cost_usd cap to crew

Revision ID: c6f2a5b39d10
Revises: b5f9d3f24e01
Create Date: 2026-07-09 12:00:00.000000

Crew-level total-cost budget across all agent nodes in one execution.
Set to 0 to leave uncapped (per-agent Budget caps in agent.py still
apply).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "c6f2a5b39d10"
down_revision = "b5f9d3f24e01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "crew",
        sa.Column(
            "max_cost_usd",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
    )


def downgrade() -> None:
    op.drop_column("crew", "max_cost_usd")
