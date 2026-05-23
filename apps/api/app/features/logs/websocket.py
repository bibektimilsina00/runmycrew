from contextlib import suppress
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket

from apps.api.app.core.logger import get_logger
from apps.api.app.core.security import get_current_user_from_token
from apps.api.app.shared.websockets import stream_redis_channel

logger = get_logger(__name__)
router = APIRouter()


@router.websocket("/workspaces/{workspace_id}/logs")
async def workspace_logs_websocket(
    websocket: WebSocket,
    workspace_id: UUID,
    token: str = Query(...),
):
    """
    WebSocket endpoint for streaming workspace-wide log events.
    Verifies the user via JWT token before accepting.
    Subscribes to Redis pub/sub for the specific workspace logs channel.
    """
    try:
        user = await get_current_user_from_token(token)
        if not user:
            await websocket.close(code=4001)  # Unauthorized
            return

        await websocket.accept()
        logger.info(f"WebSocket connected for workspace {workspace_id} logs")
        channel = f"workspace:{workspace_id}:logs"
        await stream_redis_channel(websocket, channel)

    except Exception as e:
        logger.error(
            f"Failed to initialize WebSocket for workspace {workspace_id}: {e}", exc_info=True
        )
        with suppress(Exception):
            await websocket.close(code=1011)
