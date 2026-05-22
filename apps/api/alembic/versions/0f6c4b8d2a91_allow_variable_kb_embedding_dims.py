"""allow_variable_kb_embedding_dims

Revision ID: 0f6c4b8d2a91
Revises: f055021af1b5
Create Date: 2026-05-22

Allow KB chunks to store embeddings from multiple providers.
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0f6c4b8d2a91"
down_revision: str | None = "f055021af1b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS kbchunk_embedding_idx")
    op.execute("ALTER TABLE kbchunk ALTER COLUMN embedding TYPE vector")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS kbchunk_embedding_idx")
    op.execute("UPDATE kbchunk SET embedding = NULL WHERE vector_dims(embedding) != 1536")
    op.execute("ALTER TABLE kbchunk ALTER COLUMN embedding TYPE vector(1536)")
    op.execute(
        "CREATE INDEX kbchunk_embedding_idx ON kbchunk "
        "USING hnsw (embedding vector_cosine_ops)"
    )
