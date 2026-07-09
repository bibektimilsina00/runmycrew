import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.features.personas.schemas import (
    PersonaCreate,
    PersonaOut,
    PersonaUpdate,
)
from apps.api.app.features.personas.service import PersonaService
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.features.workspaces.service import WorkspaceService
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

router = APIRouter()


@router.get("/", response_model=list[PersonaOut])
async def list_personas(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    return await PersonaService(db).list_personas(current_user, workspace)


@router.get("/public", response_model=list[PersonaOut])
async def list_public_personas(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Publicly shared personas from other workspaces."""
    return await PersonaService(db).list_public_personas(current_user, workspace)


@router.post(
    "/import/{source_id}",
    response_model=PersonaOut,
    status_code=status.HTTP_201_CREATED,
)
async def import_persona(
    source_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Copy a public persona into this workspace as an editable duplicate."""
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    return await PersonaService(db).import_persona(source_id, current_user, workspace)


@router.post("/", response_model=PersonaOut, status_code=status.HTTP_201_CREATED)
async def create_persona(
    data: PersonaCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    return await PersonaService(db).create_persona(data, current_user, workspace)


@router.get("/{persona_id}", response_model=PersonaOut)
async def get_persona(
    persona_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    return await PersonaService(db).get_persona(persona_id, current_user, workspace)


@router.patch("/{persona_id}", response_model=PersonaOut)
async def update_persona(
    persona_id: uuid.UUID,
    data: PersonaUpdate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    return await PersonaService(db).update_persona(persona_id, data, current_user, workspace)


@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_persona(
    persona_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    await PersonaService(db).delete_persona(persona_id, current_user, workspace)
