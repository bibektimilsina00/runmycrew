import uuid

from fastapi import APIRouter, Depends, Response, status

from apps.api.app.features.secrets.schemas import (
    SecretCreate,
    SecretOut,
    SecretRevealOut,
    SecretUpdate,
)
from apps.api.app.features.secrets.service import SecretService, get_secret_service
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

router = APIRouter()


@router.get("/", response_model=list[SecretOut])
async def list_secrets(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: SecretService = Depends(get_secret_service),
):
    """List workspace-scoped secrets and caller's own personal secrets."""
    return await service.list_secrets(current_user, workspace)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SecretOut)
async def create_secret(
    body: SecretCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: SecretService = Depends(get_secret_service),
):
    return await service.create_secret(body, current_user, workspace)


@router.put("/{secret_id}", response_model=SecretOut)
async def update_secret(
    secret_id: uuid.UUID,
    body: SecretUpdate,
    workspace: Workspace = Depends(get_current_workspace),
    service: SecretService = Depends(get_secret_service),
):
    return await service.update_secret(secret_id, body, workspace)


@router.delete("/{secret_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_secret(
    secret_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    service: SecretService = Depends(get_secret_service),
):
    await service.delete_secret(secret_id, workspace)


@router.get("/{secret_id}/reveal", response_model=SecretRevealOut)
async def reveal_secret(
    secret_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    service: SecretService = Depends(get_secret_service),
):
    """Return the decrypted value for a secret variable."""
    return await service.reveal_secret(secret_id, workspace)
