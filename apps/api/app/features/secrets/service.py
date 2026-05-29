import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.credential_manager.encryption.aes import AESEncryptionService
from apps.api.app.features.secrets.models import Secret
from apps.api.app.features.secrets.repository import SecretRepository
from apps.api.app.features.secrets.schemas import (
    SecretCreate,
    SecretOut,
    SecretRevealOut,
    SecretUpdate,
)
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace


class SecretService:
    """Service layer executing business logic for Secrets within the features layout."""

    def __init__(self, db: AsyncSession):
        self.repository = SecretRepository(db)
        self._enc = AESEncryptionService()

    def _normalize_key(self, key: str) -> str:
        """Normalize key name to uppercase and replace spaces/hyphens with underscores."""
        return key.strip().upper().replace(" ", "_").replace("-", "_")

    def _to_out(self, s: Secret) -> SecretOut:
        """Convert a Secret model instance to a SecretOut schema representation."""
        plain: str | None = None
        if not s.is_secret:
            try:
                plain = self._enc.decrypt(s.encrypted_value)
            except Exception:
                plain = s.encrypted_value
        return SecretOut(
            id=str(s.id),
            name=s.name,
            value=plain,
            scope=s.scope,
            is_secret=s.is_secret,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
        )

    async def list_secrets(self, current_user: User, workspace: Workspace) -> list[SecretOut]:
        """List secrets visible to the current user in the workspace."""
        secrets = await self.repository.list_by_workspace(workspace.id, current_user.id)
        return [self._to_out(s) for s in secrets]

    async def create_secret(
        self, body: SecretCreate, current_user: User, workspace: Workspace
    ) -> SecretOut:
        """Create a new secret in the workspace after normalization and validation."""
        name = self._normalize_key(body.name)
        if not name:
            raise HTTPException(status_code=400, detail="Variable name is required.")

        existing = await self.repository.get_by_name_and_workspace(name, workspace.id)
        if existing:
            raise HTTPException(status_code=409, detail=f"Variable '{name}' already exists.")

        secret = Secret(
            user_id=current_user.id,
            workspace_id=workspace.id,
            name=name,
            encrypted_value=self._enc.encrypt(body.value),
            scope=body.scope,
            is_secret=body.is_secret,
        )
        created = await self.repository.create(secret)
        return self._to_out(created)

    async def update_secret(
        self, secret_id: uuid.UUID, body: SecretUpdate, workspace: Workspace
    ) -> SecretOut:
        """Update fields of an existing secret."""
        secret = await self.repository.get_by_id_and_workspace(secret_id, workspace.id)
        if not secret:
            raise HTTPException(status_code=404, detail="Variable not found.")

        update_dict = {}

        if body.name is not None:
            new_name = self._normalize_key(body.name)
            if not new_name:
                raise HTTPException(status_code=400, detail="Variable name is required.")
            if new_name != secret.name:
                conflict = await self.repository.get_by_name_and_workspace(new_name, workspace.id)
                if conflict:
                    raise HTTPException(
                        status_code=409, detail=f"Variable '{new_name}' already exists."
                    )
            update_dict["name"] = new_name

        if body.value is not None:
            update_dict["encrypted_value"] = self._enc.encrypt(body.value)
        if body.scope is not None:
            update_dict["scope"] = body.scope
        if body.is_secret is not None:
            update_dict["is_secret"] = body.is_secret

        updated = await self.repository.update(secret, update_dict)
        return self._to_out(updated)

    async def delete_secret(self, secret_id: uuid.UUID, workspace: Workspace) -> None:
        """Delete an existing secret."""
        secret = await self.repository.get_by_id_and_workspace(secret_id, workspace.id)
        if not secret:
            raise HTTPException(status_code=404, detail="Variable not found.")
        await self.repository.delete(secret)

    async def reveal_secret(self, secret_id: uuid.UUID, workspace: Workspace) -> SecretRevealOut:
        """Reveal/decrypt the value of a secret."""
        secret = await self.repository.get_by_id_and_workspace(secret_id, workspace.id)
        if not secret:
            raise HTTPException(status_code=404, detail="Variable not found.")
        try:
            plain = self._enc.decrypt(secret.encrypted_value)
        except Exception:
            plain = secret.encrypted_value
        return SecretRevealOut(id=str(secret.id), name=secret.name, value=plain)


def get_secret_service(db: AsyncSession = Depends(get_db)) -> SecretService:
    """Dependency injection helper for FastAPI router."""
    return SecretService(db)
