import datetime
import json
from abc import ABC, abstractmethod
from typing import Any

from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)


class IEventEmitter(ABC):
    @abstractmethod
    async def emit(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit an event."""
        pass


class RedisEventEmitter(IEventEmitter):
    def __init__(self, execution_id: str, workspace_id: str | None = None):
        self.execution_id = execution_id
        self.workspace_id = workspace_id

    async def emit(self, event_type: str, data: dict[str, Any]) -> None:
        try:
            from apps.api.app.core.redis import get_redis

            redis = await get_redis()
            event = {
                "type": event_type,
                "execution_id": self.execution_id,
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z"),
                **data,
            }

            event_json = json.dumps(event)

            # Publish to execution channel
            channel = f"execution:{self.execution_id}"
            await redis.publish(channel, event_json)

            # Publish to workspace logs channel if workspace_id is provided
            if self.workspace_id:
                ws_channel = f"workspace:{self.workspace_id}:logs"
                await redis.publish(ws_channel, event_json)
        except Exception as e:
            logger.warning(f"Failed to publish execution event for {self.execution_id}: {e}")


class NullEventEmitter(IEventEmitter):
    """Fallback emitter that does nothing."""

    async def emit(self, event_type: str, data: dict[str, Any]) -> None:
        pass
