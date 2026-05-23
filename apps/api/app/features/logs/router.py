from fastapi import APIRouter, Depends, Query

from apps.api.app.features.logs.schemas import ExecutionLogOut
from apps.api.app.features.logs.service import LogsService, get_logs_service
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.shared.dependencies import get_current_workspace

router = APIRouter()


@router.get("/", response_model=list[ExecutionLogOut])
async def get_workspace_logs(
    workspace: Workspace = Depends(get_current_workspace),
    limit: int = Query(default=100, ge=1, le=1000),
    level: str | None = Query(default=None),
    service: LogsService = Depends(get_logs_service),
):
    """Retrieve execution logs for all workflows within the active workspace."""
    return await service.get_workspace_logs(workspace.id, limit=limit, level=level)
