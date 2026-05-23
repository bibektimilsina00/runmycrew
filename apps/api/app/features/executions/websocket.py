from contextlib import suppress
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.core.logger import get_logger
from apps.api.app.core.security import get_current_user_from_token
from apps.api.app.features.executions.repository import ExecutionRepository
from apps.api.app.shared.websockets import stream_redis_channel

logger = get_logger(__name__)
router = APIRouter()


@router.websocket("/executions/{execution_id}")
async def execution_websocket(
    websocket: WebSocket,
    execution_id: UUID,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for streaming execution events.
    Verifies the user via JWT token before accepting.
    Subscribes to Redis pub/sub for the specific execution.
    """
    try:
        # 1. Verify token
        user = await get_current_user_from_token(token)
        if not user:
            await websocket.close(code=4001)  # Unauthorized
            return

        await websocket.accept()
        logger.info(f"WebSocket connected for execution {execution_id}")

        terminal_status: str | None = None

        # Send initial catch-up data from DB.
        repo = ExecutionRepository(db)
        execution = await repo.get_by_id(execution_id)
        if execution:
            terminal_status = (
                execution.status if execution.status in ("completed", "failed") else None
            )
            for log in execution.logs:
                # Ensure timestamp is UTC and has 'Z' for consistent JS parsing
                ts = log.timestamp.isoformat()
                if not ts.endswith("Z") and "+00:00" not in ts:
                    ts += "Z"

                await websocket.send_json(
                    {
                        "type": "log_synced",
                        "id": str(log.id),
                        "execution_id": str(execution_id),
                        "timestamp": ts,
                        "node_id": log.node_id,
                        "level": log.level,
                        "message": log.message,
                        "payload": log.payload,
                    }
                )

        if terminal_status:
            await websocket.send_json(
                {
                    "type": f"execution_{terminal_status}",
                    "execution_id": str(execution_id),
                    "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    "status": terminal_status,
                }
            )
            logger.info(f"Execution {execution_id} already finished, closing websocket")
            await websocket.close(code=1000)
            return

        channel = f"execution:{execution_id}"
        await stream_redis_channel(
            websocket, channel, stop_event_types=("execution_completed", "execution_failed")
        )

    except Exception as e:
        logger.error(f"Failed to initialize WebSocket for {execution_id}: {e}", exc_info=True)
        with suppress(Exception):
            await websocket.close(code=1011)


@router.websocket("/workspaces/{workspace_id}/runs")
async def workspace_runs_websocket(
    websocket: WebSocket,
    workspace_id: UUID,
    token: str = Query(...),
):
    """
    WebSocket endpoint for streaming workspace-wide execution/run events.
    Verifies the user via JWT token before accepting.
    Subscribes to Redis pub/sub for the specific workspace runs channel.
    """
    try:
        user = await get_current_user_from_token(token)
        if not user:
            await websocket.close(code=4001)  # Unauthorized
            return

        await websocket.accept()
        logger.info(f"WebSocket connected for workspace {workspace_id} runs")
        channel = f"workspace:{workspace_id}:runs"
        await stream_redis_channel(websocket, channel)

    except Exception as e:
        logger.error(
            f"Failed to initialize WebSocket for workspace {workspace_id} runs: {e}", exc_info=True
        )
        with suppress(Exception):
            await websocket.close(code=1011)
