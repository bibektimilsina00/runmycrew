"""fix meta_subscribed_at tz

Revision ID: 56974735ad4f
Revises: 7c7d3fa023a6
Create Date: 2026-06-14 17:09:12.197664

The original add_meta_subscription_table migration declared
`meta_subscribed_at` as `TIMESTAMP WITHOUT TIME ZONE`, but the application
writes tz-aware `datetime.now(UTC)` values to it — asyncpg refuses to
coerce ("can't subtract offset-naive and offset-aware datetimes"), and
every subscription sync after Meta returns success crashes the workflow
save with a 500.

Align this column with the sibling `created_at` / `updated_at` columns
(which already use UTCDateTime → `TIMESTAMP WITH TIME ZONE`).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "56974735ad4f"
down_revision: str | None = "7c7d3fa023a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "metasubscription",
        "meta_subscribed_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        postgresql_using="meta_subscribed_at AT TIME ZONE 'UTC'",
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "metasubscription",
        "meta_subscribed_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        postgresql_using="meta_subscribed_at AT TIME ZONE 'UTC'",
        existing_nullable=True,
    )
