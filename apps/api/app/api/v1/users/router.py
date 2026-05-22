import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.core.database import get_db
from apps.api.app.models.user import User
from apps.api.app.repositories.user_repository import UserRepository
from apps.api.app.schemas.auth import UserOut
from apps.api.app.schemas.user import (
    ApiKeyCreate,
    ApiKeyCreateResponse,
    ApiKeyOut,
    UserUpdate,
)
from apps.api.app.services.api_key_service import ApiKeyService
from apps.api.app.services.auth_service import AuthService

router = APIRouter()


@router.put("/me", response_model=UserOut)
async def update_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update profile information of the currently authenticated user."""
    user_repo = UserRepository(db)
    auth_service = AuthService(db)

    if user_in.full_name is not None:
        current_user.full_name = user_in.full_name.strip() or None

    if user_in.password is not None:
        current_user.hashed_password = auth_service.get_password_hash(user_in.password)

    return await user_repo.update(current_user)


@router.get("/api-keys", response_model=list[ApiKeyOut])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys belonging to the current user."""
    api_key_service = ApiKeyService(db)
    return await api_key_service.list_keys(current_user.id)


@router.post("/api-keys", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new developer API key."""
    api_key_service = ApiKeyService(db)
    key_record, token_plain = await api_key_service.create_key(current_user.id, body.name)

    # Return key details with plaintext token
    return ApiKeyCreateResponse(
        id=key_record.id,
        name=key_record.name,
        key_preview=key_record.key_preview,
        created_at=key_record.created_at,
        token=token_plain,
    )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke and delete the specified developer API key."""
    api_key_service = ApiKeyService(db)
    await api_key_service.revoke_key(current_user.id, key_id)
