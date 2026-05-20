from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.models.skill import Skill
from apps.api.app.models.user import User
from apps.api.app.models.workspace import Workspace
from apps.api.app.repositories.skill_repository import SkillRepository
from apps.api.app.schemas.skill import SkillCreate, SkillUpdate


class SkillService:
    def __init__(self, db: AsyncSession):
        self.repo = SkillRepository(db)

    async def list_skills(self, user: User, workspace: Workspace) -> list[Skill]:
        return await self.repo.list_by_workspace(workspace.id)

    async def get_skill(self, skill_id: uuid.UUID, user: User, workspace: Workspace) -> Skill:
        skill = await self.repo.get_by_id_and_workspace(skill_id, workspace.id)
        if not skill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
        return skill

    async def create_skill(self, data: SkillCreate, user: User, workspace: Workspace) -> Skill:
        existing = await self.repo.get_by_name_and_workspace(data.name, workspace.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Skill '{data.name}' already exists",
            )
        skill = Skill(
            user_id=user.id,
            workspace_id=workspace.id,
            name=data.name,
            description=data.description,
            icon=data.icon,
            color=data.color,
            content=data.content,
        )
        return await self.repo.create(skill)

    async def update_skill(
        self, skill_id: uuid.UUID, data: SkillUpdate, user: User, workspace: Workspace
    ) -> Skill:
        skill = await self.get_skill(skill_id, user, workspace)
        if data.name is not None and data.name != skill.name:
            existing = await self.repo.get_by_name_and_workspace(data.name, workspace.id)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Skill '{data.name}' already exists",
                )
            skill.name = data.name
        if data.description is not None:
            skill.description = data.description
        if data.icon is not None:
            skill.icon = data.icon
        if data.color is not None:
            skill.color = data.color
        if data.content is not None:
            skill.content = data.content
        return await self.repo.update(skill)

    async def delete_skill(self, skill_id: uuid.UUID, user: User, workspace: Workspace) -> None:
        skill = await self.get_skill(skill_id, user, workspace)
        await self.repo.delete(skill)

    async def get_skills_by_ids(
        self, skill_ids: list[uuid.UUID], user: User, workspace: Workspace
    ) -> list[Skill]:
        return await self.repo.get_by_ids_and_workspace(skill_ids, workspace.id)
