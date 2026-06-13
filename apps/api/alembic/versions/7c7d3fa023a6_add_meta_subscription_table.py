"""add_meta_subscription_table

Revision ID: 7c7d3fa023a6
Revises: d4be7aa0c119
Create Date: 2026-06-13 16:39:11.033861

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

from apps.api.app.shared.sqlmodel import UTCDateTime

revision: str = "7c7d3fa023a6"
down_revision: str | None = "d4be7aa0c119"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "metasubscription",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("credential_id", sa.Uuid(), nullable=False),
        sa.Column("workflow_id", sa.Uuid(), nullable=False),
        sa.Column("node_id", sqlmodel.sql.sqltypes.AutoString(length=128), nullable=False),
        sa.Column("trigger_type", sqlmodel.sql.sqltypes.AutoString(length=128), nullable=False),
        sa.Column("object_type", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column("target_id", sqlmodel.sql.sqltypes.AutoString(length=128), nullable=False),
        sa.Column("field", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("meta_subscribed_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sqlmodel.sql.sqltypes.AutoString(length=1024), nullable=True),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.Column("updated_at", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["credential_id"], ["credential.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflow.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workflow_id", "node_id", name="uq_meta_subscription_workflow_node"),
    )
    op.create_index(
        "ix_meta_subscription_lookup",
        "metasubscription",
        ["object_type", "target_id", "field"],
        unique=False,
    )
    op.create_index(
        op.f("ix_metasubscription_credential_id"),
        "metasubscription",
        ["credential_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_metasubscription_user_id"),
        "metasubscription",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_metasubscription_workflow_id"),
        "metasubscription",
        ["workflow_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_metasubscription_workspace_id"),
        "metasubscription",
        ["workspace_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_metasubscription_workspace_id"), table_name="metasubscription")
    op.drop_index(op.f("ix_metasubscription_workflow_id"), table_name="metasubscription")
    op.drop_index(op.f("ix_metasubscription_user_id"), table_name="metasubscription")
    op.drop_index(op.f("ix_metasubscription_credential_id"), table_name="metasubscription")
    op.drop_index("ix_meta_subscription_lookup", table_name="metasubscription")
    op.drop_table("metasubscription")
