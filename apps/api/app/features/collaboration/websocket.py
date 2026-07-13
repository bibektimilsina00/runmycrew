from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.core.logger import get_logger
from apps.api.app.core.ws_auth import ws_token
from apps.api.app.features.collaboration.service import CollaborationService

logger = get_logger(__name__)
router = APIRouter()


@router.websocket("/workflows/{workflow_id}/collaboration")
async def workflow_collaboration_websocket(
    websocket: WebSocket,
    workflow_id: UUID,
    token: str | None = Query(default=None),
    workspace_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    # Token from the auth subprotocol (out of the URL/logs) or ?token=.
    resolved = ws_token(websocket, token)
    if not resolved:
        await websocket.close(code=4001)
        return
    service = CollaborationService(db)
    await service.run_socket(websocket, workflow_id, resolved, workspace_id)
