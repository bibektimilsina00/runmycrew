from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.core.logger import get_logger
from apps.api.app.features.collaboration.service import CollaborationService

logger = get_logger(__name__)
router = APIRouter()


@router.websocket("/workflows/{workflow_id}/collaboration")
async def workflow_collaboration_websocket(
    websocket: WebSocket,
    workflow_id: UUID,
    token: str = Query(...),
    workspace_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    service = CollaborationService(db)
    await service.run_socket(websocket, workflow_id, token, workspace_id)
