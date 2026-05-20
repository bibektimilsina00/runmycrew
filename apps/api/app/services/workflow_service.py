import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.logger import logger
from apps.api.app.models.user import User
from apps.api.app.models.workflow import Workflow
from apps.api.app.models.workspace import Workspace
from apps.api.app.repositories.workflow_repository import WorkflowRepository
from apps.api.app.schemas.workflow import WorkflowBatchUpdate, WorkflowCreate, WorkflowUpdate


class WorkflowService:
    def __init__(self, db: AsyncSession):
        self.repository = WorkflowRepository(db)

    async def list_workflows(self, user: User, workspace: Workspace) -> list[Workflow]:
        workflows = await self.repository.list_by_workspace(workspace.id)
        if workflows:
            return workflows
        return [await self.ensure_default_workflow(workspace)]

    async def get_workflow(self, workflow_id: uuid.UUID, user: User, workspace: Workspace) -> Workflow:
        workflow = await self.repository.get_by_id_and_workspace(workflow_id, workspace.id)
        if not workflow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
        return workflow

    async def create_workflow(self, data: WorkflowCreate, user: User, workspace: Workspace) -> Workflow:
        workflow = Workflow(
            user_id=user.id,
            workspace_id=workspace.id,
            name=data.name,
            description=data.description,
            graph=self._initial_graph(data.graph),
            folder_id=data.folder_id,
            position=data.position,
            color=data.color,
            env=data.env,
        )
        return await self.repository.create(workflow)

    async def ensure_default_workflow(self, workspace: Workspace) -> Workflow:
        workflow = Workflow(
            user_id=workspace.owner_id,
            workspace_id=workspace.id,
            name="Getting Started",
            description="Default workflow for this workspace",
            graph=self._initial_graph(None),
            position=0,
            color="#22c55e",
        )
        return await self.repository.create(workflow)

    async def update_workflow(
        self, workflow_id: uuid.UUID, data: WorkflowUpdate, user: User, workspace: Workspace
    ) -> Workflow:
        workflow = await self.get_workflow(workflow_id, user, workspace)
        if data.expected_version is not None and workflow.version_vector != data.expected_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "version_conflict",
                    "current_version": workflow.version_vector,
                    "your_version": data.expected_version,
                },
            )
        update_data = data.model_dump(exclude_unset=True, exclude={"expected_version"})
        if "graph" in update_data:
            update_data["version_vector"] = workflow.version_vector + 1
        return await self.repository.update(workflow, update_data)

    async def batch_update_workflows(
        self, data: WorkflowBatchUpdate, user: User, workspace: Workspace
    ) -> None:
        logger.info(f"Batch updating {len(data.updates)} workflows for user {user.id}")
        updates = []
        for item in data.updates:
            workflow = await self.repository.get_by_id_and_workspace(item.id, workspace.id)
            if workflow:
                update_dict = item.model_dump(exclude_unset=True, exclude={"id"})
                logger.info(f"Updating workflow {workflow.id} with {update_dict}")
                updates.append((workflow, update_dict))
            else:
                logger.warning(f"Workflow {item.id} not found or doesn't belong to user {user.id}")

        if updates:
            await self.repository.batch_update(updates)
            logger.info(f"Successfully committed batch update for {len(updates)} workflows")

    async def delete_workflow(self, workflow_id: uuid.UUID, user: User, workspace: Workspace) -> None:
        workflow = await self.get_workflow(workflow_id, user, workspace)
        await self.repository.delete(workflow)

    def _initial_graph(self, graph: dict | None) -> dict:
        if graph and graph.get("nodes"):
            return graph
        return {
            "nodes": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "trigger.manual",
                    "data": {"name": "Start", "properties": {"startWorkflow": "manual"}},
                    "position": {"x": 100, "y": 100},
                }
            ],
            "edges": [],
        }

    async def trigger_workflows(
        self,
        trigger_type: str,
        trigger_data: dict[str, Any],
        property_filters: dict[str, str] | None = None,
    ) -> list[uuid.UUID]:
        from apps.api.app.execution_engine.engine import execution_engine

        workflows = await self.repository.find_by_trigger_type(trigger_type, property_filters)
        execution_ids = []

        for workflow in workflows:
            execution_id = await execution_engine.trigger_workflow(
                workflow_id=workflow.id,
                graph=workflow.graph,
                trigger_type=trigger_type,
                input_data=trigger_data,
            )
            execution_ids.append(execution_id)

        return execution_ids
