import hashlib
import secrets
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.models.api_key import ApiKey
from apps.api.app.repositories.api_key_repository import ApiKeyRepository
from apps.api.app.services.base import BaseService


class ApiKeyService(BaseService):
    """Service layer managing developer API keys logic."""

    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.repo = ApiKeyRepository(db)

    async def list_keys(self, user_id: uuid.UUID) -> list[ApiKey]:
        """List all API keys belonging to a user."""
        return await self.repo.list_by_user(user_id)

    async def create_key(self, user_id: uuid.UUID, name: str) -> tuple[ApiKey, str]:
        """Create a new developer access key.

        Generates a high-entropy cryptographically secure random token, hashes it
        using SHA-256 for secure DB storage, masks it for preview, and saves it.

        Returns:
            A tuple of (ApiKey database record, plaintext token string).
        """
        # Generate token with prefix 'fuse_live_' and 32 url-safe secure bytes
        random_part = secrets.token_urlsafe(32)
        token = f"fuse_live_{random_part}"

        # Visual preview showing first and last 4 characters of the random part
        key_preview = f"fuse_live_{random_part[:4]}...{random_part[-4:]}"

        # Unique SHA-256 hash for O(1) query lookups
        key_hash = hashlib.sha256(token.encode()).hexdigest()

        api_key = ApiKey(
            user_id=user_id,
            name=name.strip(),
            key_hash=key_hash,
            key_preview=key_preview,
        )

        created_key = await self.repo.create(api_key)
        return created_key, token

    async def revoke_key(self, user_id: uuid.UUID, key_id: uuid.UUID) -> None:
        """Revoke and delete a user's API key."""
        api_key = await self.repo.get_by_id(key_id)
        if not api_key or api_key.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API Key not found",
            )
        await self.repo.delete(api_key)
