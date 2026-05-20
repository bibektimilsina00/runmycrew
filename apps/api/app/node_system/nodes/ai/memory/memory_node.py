from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)


class MemoryProperties(BaseModel):
    operation: str = "get"
    backend: str = "redis"
    memory_key: str = ""
    role: str = "user"
    content: str = ""
    limit: int = 10
    ttl: int = 86400


class MemoryNode(BaseNode[MemoryProperties]):
    @classmethod
    def get_properties_model(cls) -> type[MemoryProperties]:
        return MemoryProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.memory",
            name="Memory",
            category="ai",
            description="Read, write, or clear conversation memory. Shares the same memory store as the Agent node.",
            icon="BookMarked",
            color="#f59e0b",
            properties=[
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "get",
                    "options": [
                        {"label": "Get — read history", "value": "get"},
                        {"label": "Append — add a message", "value": "append"},
                        {"label": "Clear — delete all messages", "value": "clear"},
                    ],
                },
                {
                    "name": "backend",
                    "label": "Backend",
                    "type": "options",
                    "default": "redis",
                    "options": [
                        {"label": "Redis (persists across runs)", "value": "redis"},
                        {"label": "Workflow (in-execution only)", "value": "workflow"},
                    ],
                },
                {
                    "name": "memory_key",
                    "label": "Memory Key",
                    "type": "string",
                    "required": True,
                    "placeholder": "user-{{trigger.user_id}}",
                    "description": "Same key used by the Agent node to share memory.",
                },
                {
                    "name": "role",
                    "label": "Role",
                    "type": "options",
                    "default": "user",
                    "options": [
                        {"label": "User", "value": "user"},
                        {"label": "Assistant", "value": "assistant"},
                        {"label": "System", "value": "system"},
                    ],
                    "condition": {"field": "operation", "value": "append"},
                },
                {
                    "name": "content",
                    "label": "Message Content",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{trigger.message}}",
                    "condition": {"field": "operation", "value": "append"},
                },
                {
                    "name": "limit",
                    "label": "Message Limit",
                    "type": "number",
                    "default": 10,
                    "mode": "advanced",
                    "condition": {"field": "operation", "value": ["get", "append"]},
                },
                {
                    "name": "ttl",
                    "label": "TTL (seconds)",
                    "type": "number",
                    "default": 86400,
                    "mode": "advanced",
                    "condition": {"field": "backend", "value": "redis"},
                    "description": "How long to keep memory in Redis. 86400 = 24h.",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "messages", "type": "array"},
                {"label": "count", "type": "number"},
                {"label": "appended", "type": "boolean"},
                {"label": "cleared", "type": "boolean"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        key = self.props.memory_key.strip()
        if not key:
            return NodeResult(success=False, error="Memory key is required.")

        from apps.api.app.node_system.nodes.ai.agent.memory.providers import get_memory_provider

        provider = get_memory_provider(
            self.props.backend,
            context,
            ttl_seconds=self.props.ttl,
        )

        try:
            op = self.props.operation

            if op == "get":
                messages = await provider.get(key, self.props.limit)
                return NodeResult(success=True, output_data={
                    "messages": messages,
                    "count": len(messages),
                })

            elif op == "append":
                if not self.props.content.strip():
                    return NodeResult(success=False, error="Content is required for append.")
                message = {"role": self.props.role, "content": self.props.content}
                await provider.append(key, [message], self.props.limit)
                messages = await provider.get(key, self.props.limit)
                return NodeResult(success=True, output_data={
                    "messages": messages,
                    "count": len(messages),
                    "appended": True,
                })

            elif op == "clear":
                await _clear_memory(provider, key, self.props.backend)
                return NodeResult(success=True, output_data={
                    "messages": [],
                    "count": 0,
                    "cleared": True,
                })

            else:
                return NodeResult(success=False, error=f"Unknown operation: {op}")

        except Exception as e:
            logger.error(f"MemoryNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))


async def _clear_memory(provider: Any, key: str, backend: str) -> None:
    """Clear memory by overwriting with empty list."""
    if backend == "redis":
        try:
            from apps.api.app.core.redis import get_redis
            redis = await get_redis()
            await redis.delete(f"fuse:agent_memory:{key}")
        except Exception as e:
            logger.warning(f"Redis clear failed: {e}")
    else:
        # Workflow memory — overwrite with empty list
        await provider.append(key, [], limit=0)
