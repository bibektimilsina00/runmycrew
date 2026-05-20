from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.core.database import get_db
from apps.api.app.models.user import User
from apps.api.app.repositories.execution_repository import ExecutionRepository
from apps.api.app.schemas.execution import ExecutionOut

router = APIRouter()


class ResumeRequest(BaseModel):
    token: str
    input: dict[str, Any] = {}


@router.post("/{execution_id}/rerun")
async def rerun_execution(
    execution_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-trigger the same workflow with the same input data as a previous execution."""
    repo = ExecutionRepository(db)
    execution = await repo.get_by_id(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    from apps.api.app.repositories.workflow_repository import WorkflowRepository
    from apps.api.app.execution_engine.engine import execution_engine

    wf_repo = WorkflowRepository(db)
    workflow = await wf_repo.get_by_id_and_user(execution.workflow_id, current_user.id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    new_execution_id = await execution_engine.trigger_workflow(
        workflow_id=workflow.id,
        graph=workflow.graph,
        trigger_type=execution.trigger_type,
        input_data=execution.input_data or {},
    )
    return {"execution_id": str(new_execution_id), "workflow_id": str(workflow.id)}
    input: dict[str, Any] = {}


@router.get("/all")
async def list_all_executions(
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    workflow_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ExecutionRepository(db)
    rows, total = await repo.list_by_user(
        current_user.id, limit=limit, offset=offset, status=status, workflow_id=workflow_id
    )
    return {
        "executions": [
            {
                "id": str(r["id"]),
                "workflow_id": str(r["workflow_id"]),
                "workflow_name": r["workflow_name"],
                "workflow_color": r["workflow_color"],
                "status": r["status"],
                "trigger_type": r["trigger_type"],
                "started_at": r["started_at"].isoformat() if r["started_at"] else None,
                "finished_at": r["finished_at"].isoformat() if r["finished_at"] else None,
                "duration_ms": (
                    int((r["finished_at"] - r["started_at"]).total_seconds() * 1000)
                    if r["started_at"] and r["finished_at"] else None
                ),
            }
            for r in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/")
async def list_executions(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ExecutionRepository(db)
    return await repo.list_by_workflow(workflow_id)


@router.get("/{execution_id}", response_model=ExecutionOut)
async def get_execution(
    execution_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ExecutionRepository(db)
    execution = await repo.get_by_id(execution_id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    return execution


@router.post("/{execution_id}/resume", status_code=status.HTTP_202_ACCEPTED)
async def resume_execution(
    execution_id: uuid.UUID,
    body: ResumeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Resume a paused execution. No auth required — token is the secret."""
    repo = ExecutionRepository(db)
    execution = await repo.get_paused(execution_id, body.token)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paused execution not found or token invalid",
        )

    from apps.worker.app.jobs.tasks import execute_workflow
    execute_workflow.delay(
        execution_id=str(execution_id),
        workflow_id=str(execution.workflow_id),
        graph=execution.snapshot.get("graph", {}) if execution.snapshot else {},
        trigger_data={},
        resume_from=execution.paused_node_id,
        resume_input=body.input,
        snapshot=execution.snapshot,
    )
    return {"status": "resuming", "execution_id": str(execution_id)}
