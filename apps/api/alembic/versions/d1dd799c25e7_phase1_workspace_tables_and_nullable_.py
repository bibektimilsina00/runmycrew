"""phase1_workspace_tables_and_nullable_workspace_id

Revision ID: d1dd799c25e7
Revises: 0957a0bd0734
Create Date: 2026-05-20 23:58:39.071169

Phase 1 of 3 for workspace migration:
- Create workspace, workspacemember, workspaceinvite tables
- Add full_name, avatar_url to user
- Add workspace_id (nullable) to all resource tables
- Add version_vector to workflow for optimistic concurrency
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'd1dd799c25e7'
down_revision: str | None = '0957a0bd0734'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'workspace',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('is_personal', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('plan', sa.String(length=50), nullable=False, server_default='free'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_workspace_slug', 'workspace', ['slug'], unique=True)
    op.create_index('ix_workspace_owner_id', 'workspace', ['owner_id'])

    op.create_table(
        'workspacemember',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='member'),
        sa.Column('invited_by', sa.UUID(), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'user_id', name='uq_workspace_member'),
    )
    op.create_index('ix_workspacemember_workspace_id', 'workspacemember', ['workspace_id'])
    op.create_index('ix_workspacemember_user_id', 'workspacemember', ['user_id'])

    op.create_table(
        'workspaceinvite',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='member'),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('invited_by', sa.UUID(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_workspaceinvite_token', 'workspaceinvite', ['token'], unique=True)
    op.create_index('ix_workspaceinvite_workspace_id', 'workspaceinvite', ['workspace_id'])
    op.create_index('ix_workspaceinvite_email', 'workspaceinvite', ['email'])

    op.add_column('user', sa.Column('full_name', sa.String(length=200), nullable=True))
    op.add_column('user', sa.Column('avatar_url', sa.String(length=500), nullable=True))

    for table in ('workflow', 'folder', 'credential', 'secret', 'knowledgebase', 'skill'):
        op.add_column(table, sa.Column('workspace_id', sa.UUID(), nullable=True))

    op.add_column('workflow', sa.Column('version_vector', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('workflow', 'version_vector')

    for table in ('workflow', 'folder', 'credential', 'secret', 'knowledgebase', 'skill'):
        op.drop_column(table, 'workspace_id')

    op.drop_column('user', 'avatar_url')
    op.drop_column('user', 'full_name')

    op.drop_index('ix_workspaceinvite_email', table_name='workspaceinvite')
    op.drop_index('ix_workspaceinvite_workspace_id', table_name='workspaceinvite')
    op.drop_index('ix_workspaceinvite_token', table_name='workspaceinvite')
    op.drop_table('workspaceinvite')

    op.drop_index('ix_workspacemember_user_id', table_name='workspacemember')
    op.drop_index('ix_workspacemember_workspace_id', table_name='workspacemember')
    op.drop_table('workspacemember')

    op.drop_index('ix_workspace_owner_id', table_name='workspace')
    op.drop_index('ix_workspace_slug', table_name='workspace')
    op.drop_table('workspace')
