import copy
import random
import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.features.crews.models import Crew
from apps.api.app.features.crews.repository import CrewRepository
from apps.api.app.features.crews.schemas import CrewCreate, CrewUpdate
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace

CURATED_COLORS = [
    "#6366f1",  # Indigo
    "#10b981",  # Emerald
    "#f59e0b",  # Amber
    "#f43f5e",  # Rose
    "#0ea5e9",  # Sky
    "#8b5cf6",  # Violet
    "#ec4899",  # Pink
    "#3b82f6",  # Blue
]


class CrewService:
    def __init__(self, db: AsyncSession):
        self.repository = CrewRepository(db)

    async def list_crews(self, user: User, workspace: Workspace) -> list[Crew]:
        return await self.repository.list_by_workspace(workspace.id)

    async def get_crew(self, crew_id: uuid.UUID, user: User, workspace: Workspace) -> Crew:
        crew = await self.repository.get_by_id_and_workspace(crew_id, workspace.id)
        if not crew:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew not found")
        return crew

    async def create_crew(self, data: CrewCreate, user: User, workspace: Workspace) -> Crew:
        color = data.color if data.color is not None else random.choice(CURATED_COLORS)
        crew = Crew(
            user_id=user.id,
            workspace_id=workspace.id,
            name=data.name,
            description=data.description,
            graph=self._initial_graph(data.graph),
            position=data.position,
            color=color,
        )
        return await self.repository.create(crew)

    async def update_crew(
        self, crew_id: uuid.UUID, data: CrewUpdate, user: User, workspace: Workspace
    ) -> Crew:
        crew = await self.get_crew(crew_id, user, workspace)
        update_data = data.model_dump(exclude_unset=True)
        return await self.repository.update(crew, update_data)

    async def delete_crew(self, crew_id: uuid.UUID, user: User, workspace: Workspace) -> None:
        crew = await self.get_crew(crew_id, user, workspace)
        await self.repository.delete(crew)

    async def toggle_crew(self, crew_id: uuid.UUID, user: User, workspace: Workspace) -> Crew:
        crew = await self.get_crew(crew_id, user, workspace)
        return await self.repository.update(crew, {"is_active": not crew.is_active})

    async def duplicate_crew(self, crew_id: uuid.UUID, user: User, workspace: Workspace) -> Crew:
        source = await self.get_crew(crew_id, user, workspace)
        data = CrewCreate(
            name=f"{source.name} (copy)",
            description=source.description,
            graph=copy.deepcopy(source.graph),
            color=source.color,
        )
        return await self.create_crew(data, user, workspace)

    def _initial_graph(self, graph: dict | None) -> dict:
        if graph:
            return graph
        return {"nodes": [], "edges": []}


def get_crew_service(db: AsyncSession = Depends(get_db)) -> CrewService:
    return CrewService(db)
