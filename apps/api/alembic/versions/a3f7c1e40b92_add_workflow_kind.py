"""add workflow kind discriminator

Revision ID: a3f7c1e40b92
Revises: 8b2d4e1f9c7a
Create Date: 2026-07-06 09:00:00.000000

Adds the ``kind`` discriminator to ``workflow`` so loop-engineering
workflows can be told apart from normal automations (see
``docs/loop-engineering-plan.md``):

- ``automation`` (default) — the full n8n-style editor (all nodes).
- ``loop`` — the focused loop-engineering editor.

Forward-only + zero-downtime: the column is added with a server
default so existing rows backfill to ``automation`` automatically.
The application layer owns the default going forward, so the server
default is dropped once backfilled.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a3f7c1e40b92"
down_revision: str | None = "8b2d4e1f9c7a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workflow",
        sa.Column(
            "kind",
            sa.String(length=16),
            nullable=False,
            server_default="automation",
        ),
    )
    # Drop the server default once backfilled — the application layer
    # owns defaults going forward.
    op.alter_column("workflow", "kind", server_default=None)


def downgrade() -> None:
    op.drop_column("workflow", "kind")
