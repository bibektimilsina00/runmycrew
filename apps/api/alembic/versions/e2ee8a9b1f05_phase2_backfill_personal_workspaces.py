"""phase2_backfill_personal_workspaces

Revision ID: e2ee8a9b1f05
Revises: d1dd799c25e7
Create Date: 2026-05-20

Phase 2 of 3: Data migration
- Create a personal workspace for every existing user
- Add them as owner member
- Backfill workspace_id on all resource tables
"""
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = 'e2ee8a9b1f05'
down_revision: str | None = 'd1dd799c25e7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def slugify(email: str, user_id: str) -> str:
    prefix = email.split('@')[0].lower()
    prefix = ''.join(c if c.isalnum() or c == '-' else '-' for c in prefix)[:20].strip('-')
    suffix = user_id[:8]
    return f"{prefix}-{suffix}"


def personal_workspace_name(email: str, full_name: str | None) -> str:
    source = (full_name or "").strip() or email.split("@", 1)[0]
    first_name = source.split(maxsplit=1)[0] if source else "My"
    cleaned = "".join(c for c in first_name if c.isalnum() or c in {"_", "-"}).strip("_-")
    if not cleaned:
        return "My's Workspace"
    normalized = f"{cleaned[0].upper()}{cleaned[1:]}"
    return f"{normalized[:40]}'s Workspace"


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(UTC)

    users = conn.execute(sa.text("SELECT id, email, full_name FROM \"user\"")).fetchall()

    for user in users:
        user_id = str(user.id)
        workspace_id = str(uuid.uuid4())
        slug = slugify(user.email, user_id)
        name = personal_workspace_name(user.email, user.full_name)

        # Create personal workspace
        conn.execute(sa.text("""
            INSERT INTO workspace (id, name, slug, owner_id, is_personal, plan, created_at, updated_at)
            VALUES (:id, :name, :slug, :owner_id, true, 'free', :now, :now)
        """), {
            "id": workspace_id, "name": name,
            "slug": slug, "owner_id": user_id, "now": now,
        })

        # Add user as owner member
        conn.execute(sa.text("""
            INSERT INTO workspacemember (id, workspace_id, user_id, role, joined_at)
            VALUES (:id, :workspace_id, :user_id, 'owner', :now)
        """), {
            "id": str(uuid.uuid4()), "workspace_id": workspace_id,
            "user_id": user_id, "now": now,
        })

        # Backfill workspace_id on all resource tables
        for table, owner_col in [
            ('workflow', 'user_id'),
            ('folder', 'user_id'),
            ('credential', 'user_id'),
            ('secret', 'user_id'),
            ('skill', 'user_id'),
        ]:
            conn.execute(sa.text(f"""
                UPDATE {table} SET workspace_id = :workspace_id
                WHERE {owner_col} = :user_id AND workspace_id IS NULL
            """), {"workspace_id": workspace_id, "user_id": user_id})

        # knowledgebase uses user_id too
        conn.execute(sa.text("""
            UPDATE knowledgebase SET workspace_id = :workspace_id
            WHERE user_id = :user_id AND workspace_id IS NULL
        """), {"workspace_id": workspace_id, "user_id": user_id})


def downgrade() -> None:
    conn = op.get_bind()
    for table in ('workflow', 'folder', 'credential', 'secret', 'knowledgebase', 'skill'):
        conn.execute(sa.text(f"UPDATE {table} SET workspace_id = NULL"))
    conn.execute(sa.text("DELETE FROM workspacemember"))
    conn.execute(sa.text("DELETE FROM workspace WHERE is_personal = true"))
