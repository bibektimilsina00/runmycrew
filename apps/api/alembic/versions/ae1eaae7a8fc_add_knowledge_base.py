"""add_knowledge_base

Revision ID: ae1eaae7a8fc
Revises: a1f2e3d4c5b6
Create Date: 2026-05-20 16:52:16.272202

"""
from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op

revision: str = 'ae1eaae7a8fc'
down_revision: str | None = 'a1f2e3d4c5b6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        'knowledgebase',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('embedding_model', sa.String(length=100), nullable=False),
        sa.Column('embedding_provider', sa.String(length=50), nullable=False),
        sa.Column('embedding_credential_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'kbdocument',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('knowledge_base_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('chunk_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledgebase.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'kbchunk',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('knowledge_base_id', sa.UUID(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('embedding', pgvector.sqlalchemy.Vector(1536), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['kbdocument.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledgebase.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # HNSW index for fast approximate nearest-neighbor search
    op.execute(
        "CREATE INDEX kbchunk_embedding_idx ON kbchunk "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.drop_table('kbchunk')
    op.drop_table('kbdocument')
    op.drop_table('knowledgebase')
    op.execute("DROP EXTENSION IF EXISTS vector")
