from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.features.skills.models import Skill


class SkillRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_user(self, user_id: uuid.UUID) -> list[Skill]:
        result = await self.db.execute(
            select(Skill).where(Skill.user_id == user_id).order_by(Skill.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> list[Skill]:
        result = await self.db.execute(
            select(Skill)
            .where(Skill.workspace_id == workspace_id)
            .order_by(Skill.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id_and_user(self, skill_id: uuid.UUID, user_id: uuid.UUID) -> Skill | None:
        result = await self.db.execute(
            select(Skill).where(Skill.id == skill_id, Skill.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_workspace(
        self, skill_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> Skill | None:
        result = await self.db.execute(
            select(Skill).where(Skill.id == skill_id, Skill.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name_and_user(self, name: str, user_id: uuid.UUID) -> Skill | None:
        result = await self.db.execute(
            select(Skill).where(Skill.name == name, Skill.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name_and_workspace(self, name: str, workspace_id: uuid.UUID) -> Skill | None:
        result = await self.db.execute(
            select(Skill).where(Skill.name == name, Skill.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def get_by_ids_and_user(
        self, skill_ids: list[uuid.UUID], user_id: uuid.UUID
    ) -> list[Skill]:
        if not skill_ids:
            return []
        result = await self.db.execute(
            select(Skill).where(Skill.id.in_(skill_ids), Skill.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_by_ids_and_workspace(
        self, skill_ids: list[uuid.UUID], workspace_id: uuid.UUID
    ) -> list[Skill]:
        if not skill_ids:
            return []
        result = await self.db.execute(
            select(Skill).where(Skill.id.in_(skill_ids), Skill.workspace_id == workspace_id)
        )
        return list(result.scalars().all())

    async def create(self, skill: Skill) -> Skill:
        self.db.add(skill)
        await self.db.commit()
        await self.db.refresh(skill)
        return skill

    async def update(self, skill: Skill) -> Skill:
        await self.db.commit()
        await self.db.refresh(skill)
        return skill

    async def delete(self, skill: Skill) -> None:
        await self.db.delete(skill)
        await self.db.commit()
