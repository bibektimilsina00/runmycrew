import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.api.v1.workspaces.dependencies import get_current_workspace
from apps.api.app.core.database import get_db
from apps.api.app.models.user import User
from apps.api.app.models.workspace import Workspace
from apps.api.app.schemas.folder import FolderCreate, FolderOut, FolderUpdate
from apps.api.app.services.folder_service import FolderService

router = APIRouter()


@router.post("/", response_model=FolderOut)
async def create_folder(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    folder_in: FolderCreate,
) -> Any:
    service = FolderService(db)
    return await service.create_folder(
        user_id=current_user.id, workspace_id=workspace.id, schema=folder_in
    )


@router.get("/", response_model=list[FolderOut])
async def read_folders(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
) -> Any:
    service = FolderService(db)
    return await service.get_folders(workspace_id=workspace.id)


@router.get("/{folder_id}", response_model=FolderOut)
async def read_folder(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    folder_id: uuid.UUID,
) -> Any:
    service = FolderService(db)
    folder = await service.get_folder(workspace_id=workspace.id, folder_id=folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


@router.put("/{folder_id}", response_model=FolderOut)
async def update_folder(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    folder_id: uuid.UUID,
    folder_in: FolderUpdate,
) -> Any:
    service = FolderService(db)
    folder = await service.update_folder(
        workspace_id=workspace.id, folder_id=folder_id, schema=folder_in
    )
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


@router.delete("/{folder_id}")
async def delete_folder(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    folder_id: uuid.UUID,
) -> Any:
    service = FolderService(db)
    success = await service.delete_folder(workspace_id=workspace.id, folder_id=folder_id)
    if not success:
        raise HTTPException(status_code=404, detail="Folder not found")
    return {"status": "ok"}
