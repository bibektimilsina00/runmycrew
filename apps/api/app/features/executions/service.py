import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.core.redis import get_redis
from apps.api.app.execution_engine.engine import execution_engine
from apps.api.app.features.executions.repository import ExecutionRepository
from apps.api.app.features.executions.schemas import (
    ExecutionCancelResponse,
    ExecutionListAllResponse,
    ExecutionListItem,
    ExecutionOut,
    ExecutionRerunResponse,
    ExecutionResumeResponse,
    ResumeRequest,
)
from apps.api.app.features.workflows.repository import WorkflowRepository
from apps.api.app.features.workspaces.models import Workspace
from apps.worker.app.jobs.tasks import execute_workflow


class ExecutionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ExecutionRepository(db)
        self.wf_repo = WorkflowRepository(db)

    async def rerun_execution(
        self, execution_id: uuid.UUID, workspace: Workspace
    ) -> ExecutionRerunResponse:
        execution = await self.repo.get_by_id(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")

        workflow = await self.wf_repo.get_by_id_and_workspace(execution.workflow_id, workspace.id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        new_execution_id = await execution_engine.trigger_workflow(
            workflow_id=workflow.id,
            graph=workflow.graph,
            trigger_type=execution.trigger_type,
            input_data=execution.input_data or {},
        )
        return ExecutionRerunResponse(
            execution_id=str(new_execution_id), workflow_id=str(workflow.id)
        )

    async def list_all_executions(
        self,
        workspace: Workspace,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        workflow_id: uuid.UUID | None = None,
    ) -> ExecutionListAllResponse:
        rows, total = await self.repo.list_by_workspace(
            workspace.id, limit=limit, offset=offset, status=status, workflow_id=workflow_id
        )
        executions = []
        for r in rows:
            duration_ms = None
            if r["started_at"] and r["finished_at"]:
                duration_ms = int((r["finished_at"] - r["started_at"]).total_seconds() * 1000)

            executions.append(
                ExecutionListItem(
                    id=str(r["id"]),
                    workflow_id=str(r["workflow_id"]),
                    workflow_name=r["workflow_name"],
                    workflow_color=r["workflow_color"],
                    status=r["status"],
                    trigger_type=r["trigger_type"],
                    started_at=r["started_at"].isoformat() if r["started_at"] else None,
                    finished_at=r["finished_at"].isoformat() if r["finished_at"] else None,
                    duration_ms=duration_ms,
                )
            )
        return ExecutionListAllResponse(
            executions=executions,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def list_executions(
        self, workflow_id: uuid.UUID, workspace: Workspace
    ) -> list[ExecutionOut]:
        workflow = await self.wf_repo.get_by_id_and_workspace(workflow_id, workspace.id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        # Ensure we return valid ExecutionOut objects (or the repo already does if it returns Model instances)
        # Assuming the repo returns a list of Execution model instances.
        # The router will validate them against ExecutionOut schema.
        return await self.repo.list_by_workflow(workflow_id)

    async def get_execution(self, execution_id: uuid.UUID, workspace: Workspace) -> ExecutionOut:
        execution = await self.repo.get_by_id(execution_id)
        if not execution:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")

        workflow = await self.wf_repo.get_by_id_and_workspace(execution.workflow_id, workspace.id)
        if not workflow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
        return execution

    async def cancel_execution(
        self, execution_id: uuid.UUID, workspace: Workspace
    ) -> ExecutionCancelResponse:
        execution = await self.repo.get_by_id(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        if execution.status not in ("pending", "running"):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel execution with status: {execution.status}",
            )

        redis = await get_redis()
        await redis.set(f"execution:cancel:{execution_id}", "1", ex=300)

        await self.repo.update_status(execution_id, "cancelling")
        return ExecutionCancelResponse(status="cancellation requested")

    async def resume_execution(
        self, execution_id: uuid.UUID, body: ResumeRequest
    ) -> ExecutionResumeResponse:
        execution = await self.repo.get_paused(execution_id, body.token)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paused execution not found or token invalid",
            )

        execute_workflow.delay(
            execution_id=str(execution_id),
            workflow_id=str(execution.workflow_id),
            graph=execution.snapshot.get("graph", {}) if execution.snapshot else {},
            trigger_data={},
            resume_from=execution.paused_node_id,
            resume_input=body.input,
            snapshot=execution.snapshot,
        )
        return ExecutionResumeResponse(status="resuming", execution_id=str(execution_id))


def get_execution_service(db: AsyncSession = Depends(get_db)) -> ExecutionService:
    return ExecutionService(db)
