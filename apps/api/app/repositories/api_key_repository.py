import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.models.api_key import ApiKey


class ApiKeyRepository:
    """Repository for managing API Key database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_user(self, user_id: uuid.UUID) -> list[ApiKey]:
        """Retrieve all active API keys for a user, ordered by creation date descending."""
        result = await self.db.execute(
            select(ApiKey)
            .where(ApiKey.user_id == user_id)
            .order_by(ApiKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, key_id: uuid.UUID) -> ApiKey | None:
        """Retrieve an API key by its unique database ID."""
        result = await self.db.execute(select(ApiKey).where(ApiKey.id == key_id))
        return result.scalar_one_or_none()

    async def get_by_hash(self, key_hash: str) -> ApiKey | None:
        """Retrieve an API key by its unique SHA-256 hash."""
        result = await self.db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
        return result.scalar_one_or_none()

    async def create(self, api_key: ApiKey) -> ApiKey:
        """Store a new API key in the database."""
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)
        return api_key

    async def delete(self, api_key: ApiKey) -> None:
        """Revoke and delete an API key from the database."""
        await self.db.delete(api_key)
        await self.db.commit()
