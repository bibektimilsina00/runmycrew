from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response, status

from apps.api.app.features.skills.schemas import SkillCreate, SkillMetaOut, SkillOut, SkillUpdate
from apps.api.app.features.skills.service import SkillService, get_skill_service
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

router = APIRouter()


@router.get("/", response_model=list[SkillMetaOut])
async def list_skills(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: SkillService = Depends(get_skill_service),
):
    return await service.list_skills(current_user, workspace)


@router.post("/", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
async def create_skill(
    data: SkillCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: SkillService = Depends(get_skill_service),
):
    return await service.create_skill(data, current_user, workspace)


@router.get("/{skill_id}", response_model=SkillOut)
async def get_skill(
    skill_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: SkillService = Depends(get_skill_service),
):
    return await service.get_skill(skill_id, current_user, workspace)


@router.put("/{skill_id}", response_model=SkillOut)
async def update_skill(
    skill_id: uuid.UUID,
    data: SkillUpdate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: SkillService = Depends(get_skill_service),
):
    return await service.update_skill(skill_id, data, current_user, workspace)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_skill(
    skill_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: SkillService = Depends(get_skill_service),
):
    await service.delete_skill(skill_id, current_user, workspace)
