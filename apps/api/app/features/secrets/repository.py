import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.features.secrets.models import Secret


class SecretRepository:
    """Repository for handling database operations on Secret models within the secrets feature."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id_and_workspace(
        self, secret_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> Secret | None:
        """Retrieve a secret by ID within a workspace.

        Args:
            secret_id: The UUID of the secret.
            workspace_id: The UUID of the workspace.

        Returns:
            The Secret instance if found, otherwise None.
        """
        result = await self.db.execute(
            sa.select(Secret).where(Secret.id == secret_id, Secret.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name_and_workspace(self, name: str, workspace_id: uuid.UUID) -> Secret | None:
        """Retrieve a secret by name within a workspace.

        Args:
            name: The name of the secret.
            workspace_id: The UUID of the workspace.

        Returns:
            The Secret instance if found, otherwise None.
        """
        result = await self.db.execute(
            sa.select(Secret).where(Secret.workspace_id == workspace_id, Secret.name == name)
        )
        return result.scalar_one_or_none()

    async def list_by_workspace(self, workspace_id: uuid.UUID, user_id: uuid.UUID) -> list[Secret]:
        """List secrets in a workspace, including workspace scope and caller's personal scope.

        Args:
            workspace_id: The UUID of the workspace.
            user_id: The UUID of the calling user.

        Returns:
            A list of Secret instances.
        """
        result = await self.db.execute(
            sa.select(Secret)
            .where(
                Secret.workspace_id == workspace_id,
                sa.or_(
                    Secret.scope == "workspace",
                    sa.and_(Secret.scope == "personal", Secret.user_id == user_id),
                ),
            )
            .order_by(Secret.name)
        )
        return list(result.scalars().all())

    async def create(self, secret: Secret) -> Secret:
        """Persist a new secret to the database.

        Args:
            secret: The Secret instance to persist.

        Returns:
            The persisted Secret instance.
        """
        self.db.add(secret)
        await self.db.commit()
        await self.db.refresh(secret)
        return secret

    async def update(self, secret: Secret, data: dict) -> Secret:
        """Update fields on a secret and persist changes.

        Args:
            secret: The Secret instance to update.
            data: A dictionary of fields and values to update.

        Returns:
            The updated Secret instance.
        """
        for key, value in data.items():
            setattr(secret, key, value)
        await self.db.commit()
        await self.db.refresh(secret)
        return secret

    async def delete(self, secret: Secret) -> None:
        """Delete a secret from the database.

        Args:
            secret: The Secret instance to delete.
        """
        await self.db.delete(secret)
        await self.db.commit()
