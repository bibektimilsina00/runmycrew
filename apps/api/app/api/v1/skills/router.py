from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.api.v1.workspaces.dependencies import get_current_workspace
from apps.api.app.core.database import get_db
from apps.api.app.models.user import User
from apps.api.app.models.workspace import Workspace
from apps.api.app.schemas.skill import SkillCreate, SkillMetaOut, SkillOut, SkillUpdate
from apps.api.app.services.skill_service import SkillService

router = APIRouter()


@router.get("/", response_model=list[SkillMetaOut])
async def list_skills(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    service = SkillService(db)
    return await service.list_skills(current_user, workspace)


@router.post("/", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
async def create_skill(
    data: SkillCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    service = SkillService(db)
    return await service.create_skill(data, current_user, workspace)


@router.get("/{skill_id}", response_model=SkillOut)
async def get_skill(
    skill_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    service = SkillService(db)
    return await service.get_skill(skill_id, current_user, workspace)


@router.put("/{skill_id}", response_model=SkillOut)
async def update_skill(
    skill_id: uuid.UUID,
    data: SkillUpdate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    service = SkillService(db)
    return await service.update_skill(skill_id, data, current_user, workspace)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    service = SkillService(db)
    await service.delete_skill(skill_id, current_user, workspace)
