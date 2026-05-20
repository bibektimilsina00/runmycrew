import uuid

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.core.database import get_db
from apps.api.app.models.user import User
from apps.api.app.models.workspace import Workspace
from apps.api.app.services.workspace_service import WorkspaceService


async def get_current_workspace(
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    try:
        parsed = uuid.UUID(workspace_id) if workspace_id else None
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid workspace id") from exc
    return await WorkspaceService(db).resolve_workspace(current_user, parsed)
