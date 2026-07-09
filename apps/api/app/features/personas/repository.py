import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.features.personas.models import Persona


class PersonaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> list[Persona]:
        result = await self.db.execute(
            select(Persona)
            .where(Persona.workspace_id == workspace_id)
            .order_by(Persona.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id_and_workspace(
        self, persona_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> Persona | None:
        result = await self.db.execute(
            select(Persona).where(Persona.id == persona_id, Persona.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, persona_id: uuid.UUID) -> Persona | None:
        result = await self.db.execute(select(Persona).where(Persona.id == persona_id))
        return result.scalar_one_or_none()

    async def create(self, persona: Persona) -> Persona:
        self.db.add(persona)
        await self.db.commit()
        await self.db.refresh(persona)
        return persona

    async def update(self, persona: Persona, data: dict) -> Persona:
        for k, v in data.items():
            setattr(persona, k, v)
        await self.db.commit()
        await self.db.refresh(persona)
        return persona

    async def delete(self, persona: Persona) -> None:
        await self.db.delete(persona)
        await self.db.commit()
