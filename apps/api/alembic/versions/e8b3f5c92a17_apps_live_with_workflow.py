"""apps: drop published_app + repoint sessions at workflow_id

Revision ID: e8b3f5c92a17
Revises: d7a2c4b18e42
Create Date: 2026-07-09 18:00:00.000000

Refactor: the hosted-app surface no longer needs a ``PublishedApp`` row.
The workflow itself is the source of truth — its ``trigger.chat_app``
node holds the config, its ``is_active`` flag is the on/off switch, its
graph JSON is what runs. Same model as ``trigger.webhook`` / ``trigger.cron``.

- Add ``app_password_hash`` + ``app_api_key_hash`` columns to ``workflow``
  so visitor-auth secrets never touch the graph JSON (would leak in
  export).
- Repoint ``app_session`` from ``app_id`` (PublishedApp) to
  ``workflow_id``. Sessions transition cleanly by joining through the
  soon-to-be-dropped PublishedApp row.
- Drop ``app_event`` (analytics stream — not used) and ``published_app``.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "e8b3f5c92a17"
down_revision = "d7a2c4b18e42"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. New workflow columns for password + api key hashes
    op.add_column("workflow", sa.Column("app_password_hash", sa.String(), nullable=True))
    op.add_column("workflow", sa.Column("app_api_key_hash", sa.String(), nullable=True))

    # 2. Repoint app_session.app_id -> app_session.workflow_id
    op.add_column(
        "app_session",
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute(
        """
        UPDATE app_session s
        SET workflow_id = pa.workflow_id
        FROM published_app pa
        WHERE s.app_id = pa.id
        """
    )
    # Drop rows without a workflow — they came from PublishedApps whose
    # workflow was already deleted.
    op.execute("DELETE FROM app_session WHERE workflow_id IS NULL")
    op.alter_column("app_session", "workflow_id", nullable=False)
    op.create_foreign_key(
        "app_session_workflow_id_fkey",
        "app_session",
        "workflow",
        ["workflow_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_app_session_workflow_id", "app_session", ["workflow_id"])
    op.drop_index("ix_app_session_app_id", table_name="app_session")
    op.drop_constraint("app_session_app_id_fkey", "app_session", type_="foreignkey")
    op.drop_column("app_session", "app_id")

    # 3. Drop app_event (not used in the simplified design)
    op.drop_index("ix_app_event_app_id", table_name="app_event")
    op.drop_index("ix_app_event_type", table_name="app_event")
    op.drop_table("app_event")

    # 4. Drop published_app
    op.drop_index("uq_published_app_ws_slug_active", table_name="published_app")
    op.drop_index("ix_published_app_workspace_id", table_name="published_app")
    op.drop_index("ix_published_app_workflow_id", table_name="published_app")
    op.drop_index("ix_published_app_app_slug", table_name="published_app")
    op.drop_index("ix_published_app_is_active", table_name="published_app")
    op.drop_table("published_app")


def downgrade() -> None:
    raise NotImplementedError("Rollback not supported — data loss on published_app drop")
