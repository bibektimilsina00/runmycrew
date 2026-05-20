"""seed_default_workspace_workflows

Revision ID: d9a7b3c6e101
Revises: c8d5e2f1a903
Create Date: 2026-05-21

Create a starter workflow for any existing workspace that has no workflows.
"""
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "d9a7b3c6e101"
down_revision: str | None = "c8d5e2f1a903"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def starter_graph() -> dict:
    return {
        "nodes": [
            {
                "id": str(uuid4()),
                "type": "trigger.manual",
                "data": {"name": "Start", "properties": {"startWorkflow": "manual"}},
                "position": {"x": 100, "y": 100},
            }
        ],
        "edges": [],
    }


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(UTC)
    workspaces = conn.execute(
        sa.text(
            """
            SELECT w.id, w.owner_id
            FROM workspace AS w
            LEFT JOIN workflow AS wf ON wf.workspace_id = w.id
            GROUP BY w.id, w.owner_id
            HAVING count(wf.id) = 0
            """
        )
    ).fetchall()

    for workspace in workspaces:
        statement = sa.text(
            """
            INSERT INTO workflow (
                id,
                name,
                description,
                schema_version,
                graph,
                is_active,
                created_at,
                updated_at,
                position,
                color,
                version_vector,
                user_id,
                workspace_id
            )
            VALUES (
                :id,
                'Getting Started',
                'Default workflow for this workspace',
                '1.0.0',
                :graph,
                false,
                :now,
                :now,
                0,
                '#22c55e',
                0,
                :user_id,
                :workspace_id
            )
            """
        ).bindparams(sa.bindparam("graph", type_=sa.JSON()))
        conn.execute(
            statement,
            {
                "id": str(uuid4()),
                "graph": starter_graph(),
                "now": now,
                "user_id": str(workspace.owner_id),
                "workspace_id": str(workspace.id),
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DELETE FROM workflow
            WHERE name = 'Getting Started'
                AND description = 'Default workflow for this workspace'
                AND position = 0
                AND color = '#22c55e'
            """
        )
    )
