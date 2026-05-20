"""rename_personal_workspaces

Revision ID: b7c4d2e9a104
Revises: a4f2b9c8d731
Create Date: 2026-05-21

Rename legacy personal workspaces from the placeholder name to the owner's
first-name workspace label.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7c4d2e9a104"
down_revision: str | None = "a4f2b9c8d731"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE workspace AS w
            SET
                name = concat(
                    upper(left(owner_label.label, 1)),
                    substr(owner_label.label, 2),
                    '''s Workspace'
                ),
                updated_at = now()
            FROM "user" AS u
            CROSS JOIN LATERAL (
                SELECT COALESCE(
                    NULLIF(
                        regexp_replace(
                            split_part(
                                btrim(COALESCE(NULLIF(u.full_name, ''), split_part(u.email, '@', 1))),
                                ' ',
                                1
                            ),
                            '[^A-Za-z0-9_-]',
                            '',
                            'g'
                        ),
                        ''
                    ),
                    'My'
                ) AS label
            ) AS owner_label
            WHERE w.owner_id = u.id
                AND w.is_personal = true
                AND w.name = 'Personal'
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE workspace
            SET name = 'Personal', updated_at = now()
            WHERE is_personal = true
            """
        )
    )
