import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.features.crews.schemas import CrewCreate, CrewOut, CrewUpdate
from apps.api.app.features.crews.service import CrewService
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.features.workspaces.service import WorkspaceService
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

router = APIRouter()


@router.get("/", response_model=list[CrewOut])
async def list_crews(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    service = CrewService(db)
    return await service.list_crews(current_user, workspace)


@router.post("/", response_model=CrewOut, status_code=status.HTTP_201_CREATED)
async def create_crew(
    data: CrewCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    service = CrewService(db)
    return await service.create_crew(data, current_user, workspace)


@router.get("/{crew_id}", response_model=CrewOut)
async def get_crew(
    crew_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    service = CrewService(db)
    return await service.get_crew(crew_id, current_user, workspace)


@router.put("/{crew_id}", response_model=CrewOut)
async def update_crew(
    crew_id: uuid.UUID,
    data: CrewUpdate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    service = CrewService(db)
    return await service.update_crew(crew_id, data, current_user, workspace)


@router.delete("/{crew_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_crew(
    crew_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    service = CrewService(db)
    await service.delete_crew(crew_id, current_user, workspace)


@router.post("/{crew_id}/toggle", response_model=CrewOut)
async def toggle_crew(
    crew_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    service = CrewService(db)
    return await service.toggle_crew(crew_id, current_user, workspace)


@router.post("/{crew_id}/duplicate", response_model=CrewOut)
async def duplicate_crew(
    crew_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    service = CrewService(db)
    return await service.duplicate_crew(crew_id, current_user, workspace)


@router.post("/{crew_id}/run")
async def run_crew(
    crew_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    # Stage 1 foundation only — the crew execution engine lands in stage 2.
    # Validate access first so this behaves like a real endpoint once wired.
    service = CrewService(db)
    await service.get_crew(crew_id, current_user, workspace)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Crew execution is not implemented yet (stage 2).",
    )
