import asyncio
import json
from contextlib import suppress

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from apps.api.app.core.logger import get_logger
from apps.api.app.core.redis import get_redis

logger = get_logger(__name__)


async def stream_redis_channel(
    websocket: WebSocket,
    channel: str,
    stop_event_types: tuple[str, ...] = (),
) -> None:
    """Helper to stream a Redis PubSub channel to a WebSocket safely."""
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)
    logger.info(f"Subscribed to Redis channel: {channel}")

    async def listen_redis():
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])

                # Check for stop events
                if stop_event_types:
                    try:
                        data = json.loads(message["data"])
                        if data.get("type") in stop_event_types:
                            logger.info(f"Received terminal event in {channel}, closing.")
                            break
                    except Exception:
                        pass

    async def listen_websocket():
        # Keep receiving to detect client disconnects or ghost drops
        try:
            while True:
                await websocket.receive()
        except WebSocketDisconnect:
            logger.info(f"WebSocket client disconnected from {channel}")

    listen_redis_task = asyncio.create_task(listen_redis())
    listen_ws_task = asyncio.create_task(listen_websocket())

    try:
        done, pending = await asyncio.wait(
            [listen_redis_task, listen_ws_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    except Exception as e:
        logger.error(f"WebSocket error on channel {channel}: {e}", exc_info=True)
    finally:
        await pubsub.unsubscribe(channel)
        if websocket.client_state != WebSocketState.DISCONNECTED:
            with suppress(Exception):
                await websocket.close(code=1000)
