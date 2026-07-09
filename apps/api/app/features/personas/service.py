import random
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.features.personas.models import Persona
from apps.api.app.features.personas.repository import PersonaRepository
from apps.api.app.features.personas.schemas import PersonaCreate, PersonaUpdate
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace

CURATED_COLORS = [
    "#6366f1",
    "#10b981",
    "#f59e0b",
    "#f43f5e",
    "#0ea5e9",
    "#8b5cf6",
    "#ec4899",
    "#3b82f6",
]


class PersonaService:
    def __init__(self, db: AsyncSession):
        self.repository = PersonaRepository(db)

    async def list_personas(self, user: User, workspace: Workspace) -> list[Persona]:
        return await self.repository.list_by_workspace(workspace.id)

    async def get_persona(self, persona_id: uuid.UUID, user: User, workspace: Workspace) -> Persona:
        persona = await self.repository.get_by_id_and_workspace(persona_id, workspace.id)
        if not persona:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")
        return persona

    async def create_persona(
        self, data: PersonaCreate, user: User, workspace: Workspace
    ) -> Persona:
        color = data.color if data.color is not None else random.choice(CURATED_COLORS)
        persona = Persona(
            user_id=user.id,
            workspace_id=workspace.id,
            name=data.name,
            role=data.role,
            description=data.description,
            system_prompt=data.system_prompt,
            default_provider=data.default_provider,
            default_model=data.default_model,
            tools=data.tools,
            color=color,
            icon_slug=data.icon_slug,
            temperature=data.temperature,
            max_iterations=data.max_iterations,
            is_public=data.is_public,
        )
        return await self.repository.create(persona)

    async def list_public_personas(self, user: User, workspace: Workspace) -> list[Persona]:
        return await self.repository.list_public(exclude_workspace_id=workspace.id)

    async def import_persona(
        self, source_id: uuid.UUID, user: User, workspace: Workspace
    ) -> Persona:
        source = await self.repository.get_by_id(source_id)
        if not source or not source.is_public:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Public persona not found",
            )
        copy = Persona(
            user_id=user.id,
            workspace_id=workspace.id,
            name=source.name,
            role=source.role,
            description=source.description,
            system_prompt=source.system_prompt,
            default_provider=source.default_provider,
            default_model=source.default_model,
            tools=source.tools,
            color=source.color,
            icon_slug=source.icon_slug,
            temperature=source.temperature,
            max_iterations=source.max_iterations,
            is_public=False,
        )
        return await self.repository.create(copy)

    async def update_persona(
        self,
        persona_id: uuid.UUID,
        data: PersonaUpdate,
        user: User,
        workspace: Workspace,
    ) -> Persona:
        persona = await self.get_persona(persona_id, user, workspace)
        return await self.repository.update(persona, data.model_dump(exclude_unset=True))

    async def delete_persona(self, persona_id: uuid.UUID, user: User, workspace: Workspace) -> None:
        persona = await self.get_persona(persona_id, user, workspace)
        await self.repository.delete(persona)
