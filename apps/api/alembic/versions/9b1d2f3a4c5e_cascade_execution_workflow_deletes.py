"""cascade execution rows when workflows are deleted

Revision ID: 9b1d2f3a4c5e
Revises: 0f6c4b8d2a91
Create Date: 2026-05-22 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "9b1d2f3a4c5e"
down_revision: str | None = "0f6c4b8d2a91"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("executionlog_execution_id_fkey", "executionlog", type_="foreignkey")
    op.create_foreign_key(
        "executionlog_execution_id_fkey",
        "executionlog",
        "execution",
        ["execution_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("execution_workflow_id_fkey", "execution", type_="foreignkey")
    op.create_foreign_key(
        "execution_workflow_id_fkey",
        "execution",
        "workflow",
        ["workflow_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("execution_workflow_id_fkey", "execution", type_="foreignkey")
    op.create_foreign_key(
        "execution_workflow_id_fkey",
        "execution",
        "workflow",
        ["workflow_id"],
        ["id"],
    )

    op.drop_constraint("executionlog_execution_id_fkey", "executionlog", type_="foreignkey")
    op.create_foreign_key(
        "executionlog_execution_id_fkey",
        "executionlog",
        "execution",
        ["execution_id"],
        ["id"],
    )
