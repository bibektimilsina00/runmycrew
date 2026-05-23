from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.app.features.a2a.schemas import A2ACancelResponse, A2ARequest, A2AStatusResponse
from apps.api.app.features.executions.repository import (
    ExecutionRepository,
    get_execution_repository,
)
from apps.api.app.features.users.models import User
from apps.api.app.features.workflows.service import WorkflowService, get_workflow_service
from apps.api.app.shared.dependencies import get_current_user

router = APIRouter()


@router.post("/{workflow_id}", response_model=A2AStatusResponse)
async def a2a_call(
    workflow_id: uuid.UUID,
    body: A2ARequest,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
):
    """A2A endpoint — trigger a workflow synchronously and return its output."""
    workflow = await service.get_workflow(workflow_id, current_user)

    trigger_data = body.input_data or body.trigger_data
    if body.message:
        trigger_data = {"message": body.message, **trigger_data}

    from apps.api.app.execution_engine.engine import execution_engine

    execution_id = await execution_engine.trigger_workflow(
        workflow_id=workflow.id,
        graph=workflow.graph,
        trigger_type="a2a",
        input_data=trigger_data,
    )

    return A2AStatusResponse(
        execution_id=str(execution_id),
        status="running",
        output=None,
    )


@router.get("/{workflow_id}/status/{execution_id}", response_model=A2AStatusResponse)
async def a2a_get_status(
    workflow_id: uuid.UUID,
    execution_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    repo: ExecutionRepository = Depends(get_execution_repository),
):
    """Return the current status + output of an A2A execution."""
    execution = await repo.get_by_id(execution_id)
    if not execution or execution.workflow_id != workflow_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")

    return A2AStatusResponse(
        execution_id=str(execution_id),
        status=execution.status,
        output=execution.output_data,
    )


@router.delete(
    "/{workflow_id}/{execution_id}",
    response_model=A2ACancelResponse,
    status_code=status.HTTP_200_OK,
)
async def a2a_cancel(
    workflow_id: uuid.UUID,
    execution_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    repo: ExecutionRepository = Depends(get_execution_repository),
):
    """Cancel a running A2A execution by marking it failed and notifying the engine."""
    execution = await repo.get_by_id(execution_id)
    if not execution or execution.workflow_id != workflow_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")

    if execution.status not in ("pending", "running"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel execution in status '{execution.status}'",
        )

    # Set the Redis flag so the background worker actually stops processing
    from apps.api.app.core.redis import get_redis

    redis = await get_redis()
    await redis.set(f"execution:cancel:{execution_id}", "1", ex=300)

    await repo.update_status(execution_id, "cancelling")
    return A2ACancelResponse(execution_id=str(execution_id), status="cancellation requested")
