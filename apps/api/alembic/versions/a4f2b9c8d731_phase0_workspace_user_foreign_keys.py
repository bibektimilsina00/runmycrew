"""phase0_workspace_user_foreign_keys

Revision ID: a4f2b9c8d731
Revises: f3ff9b0c2a16
Create Date: 2026-05-20

Add user foreign keys for workspace ownership and invitations.
"""
from collections.abc import Sequence

from alembic import op

revision: str = "a4f2b9c8d731"
down_revision: str | None = "f3ff9b0c2a16"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_workspace_owner_id",
        "workspace",
        "user",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_workspacemember_invited_by",
        "workspacemember",
        "user",
        ["invited_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_workspaceinvite_invited_by",
        "workspaceinvite",
        "user",
        ["invited_by"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_workspaceinvite_invited_by", "workspaceinvite", type_="foreignkey")
    op.drop_constraint("fk_workspacemember_invited_by", "workspacemember", type_="foreignkey")
    op.drop_constraint("fk_workspace_owner_id", "workspace", type_="foreignkey")
