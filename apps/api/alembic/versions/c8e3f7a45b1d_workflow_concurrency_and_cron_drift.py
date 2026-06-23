"""workflow concurrency + cron drift policy

Revision ID: c8e3f7a45b1d
Revises: a1c5e9b2f0d8
Create Date: 2026-06-23 06:00:00.000000

Adds three workflow-level policy fields used by the loop-engineering
runtime (see ``docs/loop-engineering-plan.md`` sections 8.5 + 8.6):

- ``concurrency_policy`` — what happens when a fire collides with an
  in-flight run of the same workflow. ``skip`` (default) drops the
  new fire; ``queue`` polls; ``replace`` force-acquires.
- ``concurrency_queue_max_wait_seconds`` — bound on the queue policy.
- ``cron_drift_policy`` — what happens when the cron scheduler is
  late. ``latest`` (default) fires once for the current tick;
  ``catchup`` fires for every missed tick; ``skip`` does nothing
  if more than one tick was missed.

Forward-only + zero-downtime: every column is added with a server
default so existing rows are backfilled automatically.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c8e3f7a45b1d"
down_revision: str | None = "a1c5e9b2f0d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workflow",
        sa.Column(
            "concurrency_policy",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'skip'"),
        ),
    )
    op.add_column(
        "workflow",
        sa.Column(
            "concurrency_queue_max_wait_seconds",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("60"),
        ),
    )
    op.add_column(
        "workflow",
        sa.Column(
            "cron_drift_policy",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'latest'"),
        ),
    )
    # Drop the server defaults once backfilled — the application layer
    # owns defaults going forward.
    op.alter_column("workflow", "concurrency_policy", server_default=None)
    op.alter_column("workflow", "concurrency_queue_max_wait_seconds", server_default=None)
    op.alter_column("workflow", "cron_drift_policy", server_default=None)


def downgrade() -> None:
    op.drop_column("workflow", "cron_drift_policy")
    op.drop_column("workflow", "concurrency_queue_max_wait_seconds")
    op.drop_column("workflow", "concurrency_policy")
