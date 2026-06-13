import random
import uuid
from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.core.logger import logger
from apps.api.app.features.users.models import User
from apps.api.app.features.workflows.models import Workflow
from apps.api.app.features.workflows.repository import WorkflowRepository
from apps.api.app.features.workflows.schemas import (
    WorkflowBatchUpdate,
    WorkflowCreate,
    WorkflowUpdate,
)
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


class WorkflowService:
    def __init__(self, db: AsyncSession):
        self.repository = WorkflowRepository(db)

    async def list_workflows(self, user: User, workspace: Workspace) -> list[Workflow]:
        workflows = await self.repository.list_by_workspace(workspace.id)
        if workflows:
            return workflows
        return [await self.ensure_default_workflow(workspace)]

    async def get_workflow(
        self, workflow_id: uuid.UUID, user: User, workspace: Workspace
    ) -> Workflow:
        workflow = await self.repository.get_by_id_and_workspace(workflow_id, workspace.id)
        if not workflow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
        return workflow

    async def create_workflow(
        self, data: WorkflowCreate, user: User, workspace: Workspace
    ) -> Workflow:
        color = data.color if data.color is not None else random.choice(CURATED_COLORS)
        workflow = Workflow(
            user_id=user.id,
            workspace_id=workspace.id,
            name=data.name,
            description=data.description,
            graph=self._initial_graph(data.graph),
            folder_id=data.folder_id,
            position=data.position,
            color=color,
            env=data.env,
        )
        created = await self.repository.create(workflow)
        # New workflows usually start empty, but templates / duplicates
        # may already carry Meta trigger nodes. Reconcile so subscription
        # state matches the just-persisted graph.
        await self._sync_meta_subscriptions(created)
        return created

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
        graph_changed = "graph" in update_data
        if graph_changed:
            update_data["version_vector"] = workflow.version_vector + 1
        updated = await self.repository.update(workflow, update_data)
        # Reconcile Meta webhook subscriptions whenever the graph (and
        # therefore the set of trigger nodes) could have changed. Run
        # only after a successful save — never speculatively. Failures
        # bubble inside the sync but never roll back the workflow save.
        if graph_changed:
            await self._sync_meta_subscriptions(updated)
        return updated

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

    async def delete_workflow(
        self, workflow_id: uuid.UUID, user: User, workspace: Workspace
    ) -> None:
        workflow = await self.get_workflow(workflow_id, user, workspace)
        # Drop MetaSubscription rows before the cascade fires so any
        # bookkeeping (logging, audit) sees the workflow id; FK
        # ondelete=CASCADE would otherwise null-out our view of which
        # rows belonged to which workflow.
        await self._cleanup_meta_subscriptions(workflow_id)
        await self.repository.delete(workflow)

    async def _sync_meta_subscriptions(self, workflow: Workflow) -> None:
        """Best-effort reconcile. Swallow errors so a Meta API hiccup
        never blocks a workflow save — the sync function records its own
        per-row failures onto MetaSubscription.last_error."""
        try:
            from apps.api.app.features.meta.service import sync_workflow_subscriptions

            await sync_workflow_subscriptions(self.repository.db, workflow)
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"Meta subscription sync failed for workflow {workflow.id}: {exc}")

    async def _cleanup_meta_subscriptions(self, workflow_id: uuid.UUID) -> None:
        try:
            from apps.api.app.features.meta.service import cleanup_workflow_subscriptions

            await cleanup_workflow_subscriptions(self.repository.db, workflow_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"Meta subscription cleanup failed for workflow {workflow_id}: {exc}")

    def _initial_graph(self, graph: dict | None) -> dict:
        # New workflows start empty. The editor's empty-state overlay handles
        # the blank canvas and prompts the user to add their first node. Seeding
        # a Start node here meant that deleting it and then re-mounting the
        # editor (or hitting the cached workflow query) brought it back from
        # the cache before the autosave landed — confusing.
        if graph:
            return graph
        return {"nodes": [], "edges": []}

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


def get_workflow_service(db: AsyncSession = Depends(get_db)) -> WorkflowService:
    return WorkflowService(db)
