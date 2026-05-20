import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.models.credential import Credential


class CredentialRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_user(self, user_id: uuid.UUID) -> list[Credential]:
        result = await self.db.execute(
            select(Credential)
            .where(Credential.user_id == user_id)
            .order_by(Credential.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, credential_id: uuid.UUID) -> Credential | None:
        result = await self.db.execute(select(Credential).where(Credential.id == credential_id))
        return result.scalar_one_or_none()

    async def get_by_id_and_user(
        self, credential_id: uuid.UUID, user_id: uuid.UUID
    ) -> Credential | None:
        result = await self.db.execute(
            select(Credential).where(
                Credential.id == credential_id,
                Credential.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_type_and_user(
        self, credential_type: str, user_id: uuid.UUID
    ) -> Credential | None:
        result = await self.db.execute(
            select(Credential).where(
                Credential.type == credential_type,
                Credential.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, credential: Credential) -> Credential:
        self.db.add(credential)
        await self.db.commit()
        await self.db.refresh(credential)
        return credential

    async def update(self, credential: Credential) -> Credential:
        await self.db.commit()
        await self.db.refresh(credential)
        return credential

    async def delete(self, credential: Credential) -> None:
        await self.db.delete(credential)
        await self.db.commit()
