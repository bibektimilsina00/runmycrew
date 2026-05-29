"""normalize_personal_workspace_names

Revision ID: c8d5e2f1a903
Revises: b7c4d2e9a104
Create Date: 2026-05-21

Recompute personal workspace labels after preserving registration full names.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c8d5e2f1a903"
down_revision: str | None = "b7c4d2e9a104"
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
                AND (
                    w.name = 'Personal'
                    OR w.name = concat(split_part(u.email, '@', 1), '''s Workspace')
                )
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE workspace AS w
            SET name = concat(split_part(u.email, '@', 1), '''s Workspace'), updated_at = now()
            FROM "user" AS u
            WHERE w.owner_id = u.id
                AND w.is_personal = true
            """
        )
    )
