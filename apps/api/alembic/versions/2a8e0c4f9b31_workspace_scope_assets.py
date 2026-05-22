"""workspace scope assets

Revision ID: 2a8e0c4f9b31
Revises: 9b1d2f3a4c5e
Create Date: 2026-05-22 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2a8e0c4f9b31"
down_revision: str | None = "9b1d2f3a4c5e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DELETE FROM asset")
    op.add_column("asset", sa.Column("workspace_id", sa.UUID(), nullable=False))
    op.add_column(
        "asset",
        sa.Column("source_type", sa.String(length=50), server_default="uploaded", nullable=False),
    )
    op.create_index(op.f("ix_asset_workspace_id"), "asset", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_asset_user_id"), "asset", ["user_id"], unique=False)
    op.create_foreign_key(
        "asset_workspace_id_fkey",
        "asset",
        "workspace",
        ["workspace_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column("asset", "source_type", server_default=None)


def downgrade() -> None:
    op.drop_constraint("asset_workspace_id_fkey", "asset", type_="foreignkey")
    op.drop_index(op.f("ix_asset_user_id"), table_name="asset")
    op.drop_index(op.f("ix_asset_workspace_id"), table_name="asset")
    op.drop_column("asset", "source_type")
    op.drop_column("asset", "workspace_id")
