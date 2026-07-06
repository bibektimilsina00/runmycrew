import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.features.crews.models import Crew, CrewExecution


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


class CrewExecutionRepository:
    """History + status tracking for crew runs.

    Mirrors ExecutionRepository (workflows) but backed by the
    `crew_execution` table via the CrewExecution model.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, crew_execution: CrewExecution) -> CrewExecution:
        self.db.add(crew_execution)
        await self.db.commit()
        await self.db.refresh(crew_execution)
        return crew_execution

    async def get_by_id(self, crew_execution_id: uuid.UUID) -> CrewExecution | None:
        result = await self.db.execute(
            select(CrewExecution).where(CrewExecution.id == crew_execution_id)
        )
        return result.scalar_one_or_none()

    async def list_by_crew(self, crew_id: uuid.UUID) -> list[CrewExecution]:
        result = await self.db.execute(
            select(CrewExecution)
            .where(CrewExecution.crew_id == crew_id)
            .order_by(CrewExecution.started_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        crew_execution_id: uuid.UUID,
        status: str,
        output_data: dict | None = None,
        finished: bool = False,
    ) -> None:
        result = await self.db.execute(
            select(CrewExecution).where(CrewExecution.id == crew_execution_id)
        )
        crew_execution = result.scalar_one_or_none()
        if crew_execution:
            crew_execution.status = status
            if status == "running":
                crew_execution.started_at = datetime.now(UTC)
            if finished or status in ("completed", "failed", "cancelled"):
                crew_execution.finished_at = datetime.now(UTC)
            if output_data is not None:
                crew_execution.output_data = output_data
            await self.db.commit()

    async def save_pause(
        self,
        crew_execution_id: uuid.UUID,
        node_id: str,
        resume_token: str,
        resume_schema: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> None:
        result = await self.db.execute(
            select(CrewExecution).where(CrewExecution.id == crew_execution_id)
        )
        crew_execution = result.scalar_one_or_none()
        if crew_execution:
            crew_execution.status = "paused"
            crew_execution.paused_node_id = node_id
            crew_execution.resume_token = resume_token
            crew_execution.resume_schema = resume_schema
            crew_execution.snapshot = snapshot
            await self.db.commit()
