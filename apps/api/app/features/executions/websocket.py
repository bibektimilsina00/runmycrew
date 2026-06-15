import asyncio
import json
from contextlib import suppress
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketState

from apps.api.app.core.database import get_db
from apps.api.app.core.logger import get_logger
from apps.api.app.core.redis import get_redis
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

        # CRITICAL ORDERING: subscribe to Redis BEFORE the catch-up read.
        # Pub/sub buffers messages from `subscribe()` onward, so events the
        # worker publishes during catch-up still replay on `listen()`. The
        # old order (catch-up → subscribe) dropped any event fired in that
        # window — workers routinely emit `execution_started` and the
        # terminal `execution_failed` within the first 200ms after
        # dispatch, which left the editor stuck on "Executing…" because
        # the terminal event was published before the subscribe landed.
        channel = f"execution:{execution_id}"
        redis = await get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel)
        logger.info(f"Subscribed to Redis channel: {channel}")

        try:
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

            await _stream_pubsub(
                websocket,
                pubsub,
                channel,
                stop_event_types=("execution_completed", "execution_failed"),
            )
        finally:
            with suppress(Exception):
                await pubsub.unsubscribe(channel)

    except Exception as e:
        logger.error(f"Failed to initialize WebSocket for {execution_id}: {e}", exc_info=True)
        with suppress(Exception):
            await websocket.close(code=1011)


async def _stream_pubsub(
    websocket: WebSocket,
    pubsub,
    channel: str,
    stop_event_types: tuple[str, ...] = (),
) -> None:
    """Stream an already-subscribed Redis pubsub to a WebSocket.

    Mirrors `shared.websockets.stream_redis_channel` but takes a
    caller-owned pubsub so the WS handler can subscribe before the
    catch-up read (avoiding the publish-before-subscribe race).
    """

    async def listen_redis():
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            await websocket.send_text(message["data"])
            if stop_event_types:
                try:
                    data = json.loads(message["data"])
                    if data.get("type") in stop_event_types:
                        logger.info(f"Received terminal event in {channel}, closing.")
                        break
                except Exception:
                    pass

    async def listen_ws():
        try:
            while True:
                await websocket.receive()
        except (WebSocketDisconnect, RuntimeError):
            # RuntimeError covers "Cannot call receive once a disconnect
            # message has been received" — Starlette raises that on a
            # second receive() after the client already vanished.
            logger.info(f"WebSocket client disconnected from {channel}")

    redis_task = asyncio.create_task(listen_redis())
    ws_task = asyncio.create_task(listen_ws())
    try:
        _done, pending = await asyncio.wait(
            [redis_task, ws_task], return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
    finally:
        if websocket.client_state != WebSocketState.DISCONNECTED:
            with suppress(Exception):
                await websocket.close(code=1000)


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
