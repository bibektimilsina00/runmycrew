import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from apps.api.app.features.folders.schemas import (
    FolderCreate,
    FolderDeleteResponse,
    FolderOut,
    FolderUpdate,
)
from apps.api.app.features.folders.service import FolderService, get_folder_service
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

router = APIRouter()


@router.post("/", response_model=FolderOut)
async def create_folder(
    *,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: FolderService = Depends(get_folder_service),
    folder_in: FolderCreate,
) -> Any:
    return await service.create_folder(
        user_id=current_user.id, workspace_id=workspace.id, schema=folder_in
    )


@router.get("/", response_model=list[FolderOut])
async def read_folders(
    *,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: FolderService = Depends(get_folder_service),
) -> Any:
    return await service.get_folders(workspace_id=workspace.id)


@router.get("/{folder_id}", response_model=FolderOut)
async def read_folder(
    *,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: FolderService = Depends(get_folder_service),
    folder_id: uuid.UUID,
) -> Any:
    folder = await service.get_folder(workspace_id=workspace.id, folder_id=folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


@router.put("/{folder_id}", response_model=FolderOut)
async def update_folder(
    *,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: FolderService = Depends(get_folder_service),
    folder_id: uuid.UUID,
    folder_in: FolderUpdate,
) -> Any:
    folder = await service.update_folder(
        workspace_id=workspace.id, folder_id=folder_id, schema=folder_in
    )
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


@router.delete("/{folder_id}", response_model=FolderDeleteResponse)
async def delete_folder(
    *,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: FolderService = Depends(get_folder_service),
    folder_id: uuid.UUID,
) -> Any:
    success = await service.delete_folder(workspace_id=workspace.id, folder_id=folder_id)
    if not success:
        raise HTTPException(status_code=404, detail="Folder not found")
    return FolderDeleteResponse(status="ok")
