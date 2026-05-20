"""add_secrets

Revision ID: 0957a0bd0734
Revises: afe6beec9e80
Create Date: 2026-05-20 20:24:50.671532

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0957a0bd0734'
down_revision: Union[str, None] = 'afe6beec9e80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'secret',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('encrypted_value', sa.String(length=2000), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_secret_user_id', 'secret', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_secret_user_id', table_name='secret')
    op.drop_table('secret')
