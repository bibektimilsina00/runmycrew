import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.features.workflows.models import Workflow


class WorkflowRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, workflow_id: uuid.UUID) -> Workflow | None:
        result = await self.db.execute(select(Workflow).where(Workflow.id == workflow_id))
        return result.scalar_one_or_none()

    async def get_by_id_and_user(
        self, workflow_id: uuid.UUID, user_id: uuid.UUID
    ) -> Workflow | None:
        result = await self.db.execute(
            select(Workflow).where(
                Workflow.id == workflow_id,
                Workflow.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_workspace(
        self, workflow_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> Workflow | None:
        result = await self.db.execute(
            select(Workflow).where(
                Workflow.id == workflow_id,
                Workflow.workspace_id == workspace_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID) -> list[Workflow]:
        result = await self.db.execute(
            select(Workflow)
            .where(Workflow.user_id == user_id)
            .order_by(Workflow.position.asc(), Workflow.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> list[Workflow]:
        result = await self.db.execute(
            select(Workflow)
            .where(Workflow.workspace_id == workspace_id)
            .order_by(Workflow.position.asc(), Workflow.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, workflow: Workflow) -> Workflow:
        self.db.add(workflow)
        await self.db.commit()
        await self.db.refresh(workflow)
        return workflow

    async def update(self, workflow: Workflow, data: dict) -> Workflow:
        for key, value in data.items():
            setattr(workflow, key, value)
        await self.db.commit()
        await self.db.refresh(workflow)
        return workflow

    async def batch_update(self, updates: list[tuple[Workflow, dict]]) -> None:
        for workflow, data in updates:
            for key, value in data.items():
                setattr(workflow, key, value)
            self.db.add(workflow)
        await self.db.commit()

    async def delete(self, workflow: Workflow) -> None:
        await self.db.delete(workflow)
        await self.db.commit()

    async def find_by_trigger_type(
        self,
        trigger_type: str,
        property_filters: dict[str, str] | None = None,
        active_only: bool = True,
    ) -> list[Workflow]:
        # For now, simple list and filter to keep it database-agnostic in the schema
        # In production, we'd use JSONB queries: Workflow.graph['nodes'].contains([{'type': trigger_type}])
        statement = select(Workflow)
        if active_only:
            statement = statement.where(Workflow.is_active.is_(True))

        result = await self.db.execute(statement)
        workflows = list(result.scalars().all())

        matches = []
        for wf in workflows:
            nodes = wf.graph.get("nodes", [])
            for node in nodes:
                if node.get("type") == trigger_type:
                    if property_filters:
                        props = node.get("data", {}).get("properties", {})
                        if all(props.get(k) == v for k, v in property_filters.items()):
                            matches.append(wf)
                            break
                    else:
                        matches.append(wf)
                        break
        return matches
