import uuid

import sqlalchemy as sa
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.features.credentials.manager.encryption.aes import AESEncryptionService
from apps.api.app.features.secrets.models import Secret
from apps.api.app.features.secrets.schemas import (
    SecretCreate,
    SecretOut,
    SecretRevealOut,
    SecretUpdate,
)
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace


class SecretService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._enc = AESEncryptionService()

    def _normalize_key(self, key: str) -> str:
        return key.strip().upper().replace(" ", "_").replace("-", "_")

    def _to_out(self, s: Secret) -> SecretOut:
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
        result = await self.db.execute(
            sa.select(Secret)
            .where(
                Secret.workspace_id == workspace.id,
                sa.or_(
                    Secret.scope == "workspace",
                    sa.and_(Secret.scope == "personal", Secret.user_id == current_user.id),
                ),
            )
            .order_by(Secret.name)
        )
        return [self._to_out(s) for s in result.scalars().all()]

    async def create_secret(
        self, body: SecretCreate, current_user: User, workspace: Workspace
    ) -> SecretOut:
        name = self._normalize_key(body.name)
        if not name:
            raise HTTPException(status_code=400, detail="Variable name is required.")

        existing = await self.db.execute(
            sa.select(Secret).where(Secret.workspace_id == workspace.id, Secret.name == name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"Variable '{name}' already exists.")

        secret = Secret(
            user_id=current_user.id,
            workspace_id=workspace.id,
            name=name,
            encrypted_value=self._enc.encrypt(body.value),
            scope=body.scope,
            is_secret=body.is_secret,
        )
        self.db.add(secret)
        await self.db.commit()
        await self.db.refresh(secret)
        return self._to_out(secret)

    async def update_secret(
        self, secret_id: uuid.UUID, body: SecretUpdate, workspace: Workspace
    ) -> SecretOut:
        result = await self.db.execute(
            sa.select(Secret).where(Secret.id == secret_id, Secret.workspace_id == workspace.id)
        )
        secret = result.scalar_one_or_none()
        if not secret:
            raise HTTPException(status_code=404, detail="Variable not found.")

        if body.name is not None:
            new_name = self._normalize_key(body.name)
            if new_name != secret.name:
                conflict = await self.db.execute(
                    sa.select(Secret).where(
                        Secret.workspace_id == workspace.id,
                        Secret.name == new_name,
                        Secret.id != secret_id,
                    )
                )
                if conflict.scalar_one_or_none():
                    raise HTTPException(
                        status_code=409, detail=f"Variable '{new_name}' already exists."
                    )
            secret.name = new_name

        if body.value is not None:
            secret.encrypted_value = self._enc.encrypt(body.value)
        if body.scope is not None:
            secret.scope = body.scope
        if body.is_secret is not None:
            secret.is_secret = body.is_secret

        await self.db.commit()
        await self.db.refresh(secret)
        return self._to_out(secret)

    async def delete_secret(self, secret_id: uuid.UUID, workspace: Workspace) -> None:
        result = await self.db.execute(
            sa.select(Secret).where(Secret.id == secret_id, Secret.workspace_id == workspace.id)
        )
        secret = result.scalar_one_or_none()
        if not secret:
            raise HTTPException(status_code=404, detail="Variable not found.")
        await self.db.delete(secret)
        await self.db.commit()

    async def reveal_secret(self, secret_id: uuid.UUID, workspace: Workspace) -> SecretRevealOut:
        result = await self.db.execute(
            sa.select(Secret).where(Secret.id == secret_id, Secret.workspace_id == workspace.id)
        )
        secret = result.scalar_one_or_none()
        if not secret:
            raise HTTPException(status_code=404, detail="Variable not found.")
        try:
            plain = self._enc.decrypt(secret.encrypted_value)
        except Exception:
            plain = secret.encrypted_value
        return SecretRevealOut(id=str(secret.id), name=secret.name, value=plain)


def get_secret_service(db: AsyncSession = Depends(get_db)) -> SecretService:
    return SecretService(db)
