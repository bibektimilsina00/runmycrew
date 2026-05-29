"""convert naive timestamps to timestamptz

Revision ID: d4be7aa0c119
Revises: ee615c3211b2
Create Date: 2026-05-28 14:56:16.200753

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4be7aa0c119"
down_revision: str | None = "ee615c3211b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Every naive timestamp column. The three execution columns
# (execution.started_at/finished_at, executionlog.timestamp) are already
# timestamptz and are intentionally excluded.
COLUMNS: list[tuple[str, str]] = [
    ("apikey", "created_at"),
    ("asset", "created_at"),
    ("asset", "updated_at"),
    ("auditlog", "created_at"),
    ("copilotsession", "created_at"),
    ("copilotsession", "updated_at"),
    ("credential", "created_at"),
    ("credential", "updated_at"),
    ("datatable", "created_at"),
    ("datatable", "updated_at"),
    ("folder", "created_at"),
    ("folder", "updated_at"),
    ("kbdocument", "created_at"),
    ("knowledgebase", "created_at"),
    ("knowledgebase", "updated_at"),
    ("secret", "created_at"),
    ("secret", "updated_at"),
    ("skill", "created_at"),
    ("skill", "updated_at"),
    ("tablecolumn", "created_at"),
    ("tablerow", "created_at"),
    ("tablerow", "updated_at"),
    ("user", "created_at"),
    ("workflow", "created_at"),
    ("workflow", "updated_at"),
    ("workflowversion", "created_at"),
    ("workspace", "created_at"),
    ("workspace", "updated_at"),
    ("workspaceinvite", "accepted_at"),
    ("workspaceinvite", "created_at"),
    ("workspaceinvite", "expires_at"),
    ("workspacemember", "joined_at"),
]

# Columns that were left nullable but always carry a value; aligned NOT NULL
# with the rest of the created_at/updated_at columns.
TIGHTEN_NOT_NULL: list[tuple[str, str]] = [
    ("asset", "created_at"),
    ("asset", "updated_at"),
    ("copilotsession", "created_at"),
    ("copilotsession", "updated_at"),
]


def upgrade() -> None:
    # Existing naive values were written as UTC wall-clock, so reinterpret them
    # as UTC when widening the column to timestamptz.
    for table, column in COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=True),
            postgresql_using=f"\"{column}\" AT TIME ZONE 'UTC'",
        )

    for table, column in TIGHTEN_NOT_NULL:
        op.execute(f'UPDATE "{table}" SET "{column}" = now() WHERE "{column}" IS NULL')
        op.alter_column(table, column, existing_type=sa.DateTime(timezone=True), nullable=False)


def downgrade() -> None:
    for table, column in TIGHTEN_NOT_NULL:
        op.alter_column(table, column, existing_type=sa.DateTime(timezone=True), nullable=True)

    for table, column in COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=False),
            postgresql_using=f"\"{column}\" AT TIME ZONE 'UTC'",
        )
