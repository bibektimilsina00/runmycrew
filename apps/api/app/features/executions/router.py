from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status

from apps.api.app.features.executions.schemas import (
    ExecutionCancelResponse,
    ExecutionListAllResponse,
    ExecutionOut,
    ExecutionRerunResponse,
    ExecutionResumeResponse,
    ResumeRequest,
)
from apps.api.app.features.executions.service import ExecutionService, get_execution_service
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

router = APIRouter()


@router.post("/{execution_id}/rerun", response_model=ExecutionRerunResponse)
async def rerun_execution(
    execution_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: ExecutionService = Depends(get_execution_service),
):
    """Re-trigger the same workflow with the same input data as a previous execution."""
    return await service.rerun_execution(execution_id, workspace)


@router.get("/all", response_model=ExecutionListAllResponse)
async def list_all_executions(
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    workflow_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: ExecutionService = Depends(get_execution_service),
):
    return await service.list_all_executions(
        workspace, limit=limit, offset=offset, status=status, workflow_id=workflow_id
    )


@router.get("/", response_model=list[ExecutionOut])
async def list_executions(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: ExecutionService = Depends(get_execution_service),
):
    return await service.list_executions(workflow_id, workspace)


@router.get("/{execution_id}", response_model=ExecutionOut)
async def get_execution(
    execution_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: ExecutionService = Depends(get_execution_service),
):
    return await service.get_execution(execution_id, workspace)


@router.post("/{execution_id}/cancel", response_model=ExecutionCancelResponse)
async def cancel_execution(
    execution_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: ExecutionService = Depends(get_execution_service),
):
    return await service.cancel_execution(execution_id, workspace)


@router.post(
    "/{execution_id}/resume",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ExecutionResumeResponse,
)
async def resume_execution(
    execution_id: uuid.UUID,
    body: ResumeRequest,
    service: ExecutionService = Depends(get_execution_service),
):
    """Resume a paused execution. No auth required — token is the secret."""
    return await service.resume_execution(execution_id, body)
