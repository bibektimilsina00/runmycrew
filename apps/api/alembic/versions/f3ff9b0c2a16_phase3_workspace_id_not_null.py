"""phase3_workspace_id_not_null

Revision ID: f3ff9b0c2a16
Revises: e2ee8a9b1f05
Create Date: 2026-05-20

Phase 3 of 3: Make workspace_id NOT NULL and add FKs + indexes
"""
from collections.abc import Sequence

from alembic import op

revision: str = 'f3ff9b0c2a16'
down_revision: str | None = 'e2ee8a9b1f05'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ['workflow', 'folder', 'credential', 'secret', 'knowledgebase', 'skill']


def upgrade() -> None:
    for table in TABLES:
        # Make NOT NULL
        op.alter_column(table, 'workspace_id', nullable=False)
        # Add FK
        op.create_foreign_key(
            f'fk_{table}_workspace_id',
            table, 'workspace',
            ['workspace_id'], ['id'],
            ondelete='CASCADE',
        )
        # Add index for scoped queries
        op.create_index(f'ix_{table}_workspace_id', table, ['workspace_id'])


def downgrade() -> None:
    for table in TABLES:
        op.drop_index(f'ix_{table}_workspace_id', table_name=table)
        op.drop_constraint(f'fk_{table}_workspace_id', table, type_='foreignkey')
        op.alter_column(table, 'workspace_id', nullable=True)
