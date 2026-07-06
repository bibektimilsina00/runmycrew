import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.features.crews.models import Crew


class CrewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, crew_id: uuid.UUID) -> Crew | None:
        result = await self.db.execute(select(Crew).where(Crew.id == crew_id))
        return result.scalar_one_or_none()

    async def get_by_id_and_workspace(
        self, crew_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> Crew | None:
        result = await self.db.execute(
            select(Crew).where(
                Crew.id == crew_id,
                Crew.workspace_id == workspace_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> list[Crew]:
        result = await self.db.execute(
            select(Crew)
            .where(Crew.workspace_id == workspace_id)
            .order_by(Crew.position.asc(), Crew.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, crew: Crew) -> Crew:
        self.db.add(crew)
        await self.db.commit()
        await self.db.refresh(crew)
        return crew

    async def update(self, crew: Crew, data: dict) -> Crew:
        for key, value in data.items():
            setattr(crew, key, value)
        await self.db.commit()
        await self.db.refresh(crew)
        return crew

    async def delete(self, crew: Crew) -> None:
        await self.db.delete(crew)
        await self.db.commit()
