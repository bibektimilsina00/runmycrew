from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.workspaces.dependencies import get_current_workspace
from apps.api.app.core.database import get_db
from apps.api.app.models.workspace import Workspace
from apps.api.app.repositories.execution_repository import ExecutionRepository

router = APIRouter()


@router.get("/")
async def get_workspace_logs(
    *,
    db: AsyncSession = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
    limit: int = Query(default=100, ge=1, le=1000),
    level: str | None = Query(default=None),
) -> Any:
    """Retrieve execution logs for all workflows within the active workspace."""
    repo = ExecutionRepository(db)
    
    # Map frontend levels to database levels
    db_level = None
    if level:
        if level == "err":
            db_level = "error"
        elif level in ("info", "warn"):
            db_level = level

    logs = await repo.get_logs_by_workspace(
        workspace_id=workspace.id,
        limit=limit,
        level=db_level,
    )
    return logs
