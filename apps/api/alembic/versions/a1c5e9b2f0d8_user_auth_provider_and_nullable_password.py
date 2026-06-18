"""user auth_provider + nullable hashed_password

Revision ID: a1c5e9b2f0d8
Revises: fb4e4bafc6d6
Create Date: 2026-06-18 13:55:00.000000

Make `hashed_password` nullable so OAuth-only accounts (Google
sign-in) can exist without a Fuse password, and add an
`auth_provider` column ("password" | "google" | ...) so the UI +
backend can tell native + federated identities apart.

Existing rows are backfilled to `auth_provider = 'password'` —
they all registered with email + password, by definition.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1c5e9b2f0d8"
down_revision: str | None = "fb4e4bafc6d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop NOT NULL on hashed_password so Google-only users can land
    # in the table without a password we'd never use.
    op.alter_column("user", "hashed_password", existing_type=sa.String(), nullable=True)

    # Add auth_provider with a server-side default so existing rows get
    # 'password' on commit; then drop the server default (Python-side
    # default on the model is enough for new rows going forward).
    op.add_column(
        "user",
        sa.Column(
            "auth_provider",
            sa.String(length=32),
            nullable=False,
            server_default="password",
        ),
    )
    op.alter_column("user", "auth_provider", server_default=None)


def downgrade() -> None:
    op.drop_column("user", "auth_provider")
    # Caller must guarantee no NULL hashed_passwords exist before
    # reverting; otherwise the ALTER will fail with a NOT NULL
    # violation. We deliberately don't UPDATE-fill here — losing
    # OAuth-only accounts on rollback would be surprising.
    op.alter_column("user", "hashed_password", existing_type=sa.String(), nullable=False)
