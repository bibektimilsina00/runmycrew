"""add_workflow_versions

Revision ID: afe6beec9e80
Revises: ae1eaae7a8fc
Create Date: 2026-05-20 19:34:26.045775

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'afe6beec9e80'
down_revision: str | None = 'ae1eaae7a8fc'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'workflowversion',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workflow_id', sa.UUID(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=200), nullable=True),
        sa.Column('graph', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflow.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_workflowversion_workflow_id', 'workflowversion', ['workflow_id'])


def downgrade() -> None:
    op.drop_index('ix_workflowversion_workflow_id', table_name='workflowversion')
    op.drop_table('workflowversion')
