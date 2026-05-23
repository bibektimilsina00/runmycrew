import uuid

from fastapi import APIRouter, Depends, Response, status

from apps.api.app.features.api_keys.schemas import (
    ApiKeyCreate,
    ApiKeyCreateResponse,
    ApiKeyOut,
)
from apps.api.app.features.api_keys.service import ApiKeyService, get_api_key_service
from apps.api.app.features.users.models import User
from apps.api.app.shared.dependencies import get_current_user

router = APIRouter()


@router.get("", response_model=list[ApiKeyOut])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    service: ApiKeyService = Depends(get_api_key_service),
):
    """List all API keys belonging to the current user."""
    return await service.list_keys(current_user.id)


@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    service: ApiKeyService = Depends(get_api_key_service),
):
    """Generate a new developer API key."""
    key_record, token_plain = await service.create_key(current_user.id, body.name)

    # Return key details with plaintext token
    return ApiKeyCreateResponse(
        id=key_record.id,
        name=key_record.name,
        key_preview=key_record.key_preview,
        created_at=key_record.created_at,
        token=token_plain,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def revoke_api_key(
    key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ApiKeyService = Depends(get_api_key_service),
):
    """Revoke and delete the specified developer API key."""
    await service.revoke_key(current_user.id, key_id)
