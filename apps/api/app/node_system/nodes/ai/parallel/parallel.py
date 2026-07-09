from __future__ import annotations

import asyncio
import json
import uuid as _uuid
from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.ai.parallel import COLOR, ICON_SLUG, NAME

logger = get_logger(__name__)


class ParallelProperties(BaseModel):
    # Where the task list comes from. Empty = read ``input_data["tasks"]``
    # (Task Planner output). Non-empty = JSON string / expression the runtime
    # already resolved for us.
    tasks_input: list[dict[str, Any]] | str | None = Field(default_factory=list)
    # ``{"researcher": "<persona_uuid>", ...}`` — maps a task's assignee_role
    # to the persona used for that fan-out.
    persona_map: dict[str, str] | str = Field(default_factory=dict)
    # Fallback persona for tasks whose role has no map entry.
    default_persona_id: str | None = None
    max_concurrent: int = 4
    shared_context: str = ""


class ParallelNode(BaseNode[ParallelProperties]):
    @classmethod
    def get_properties_model(cls) -> type[ParallelProperties]:
        return ParallelProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="ai.parallel",
            name=NAME,
            category="ai",
            description=(
                "Run one agent per task in parallel. Each task is dispatched to the persona "
                "assigned in the map (or the fallback persona), then results are collected."
            ),
            icon=ICON_SLUG,
            color=COLOR,
            properties=[
                {
                    "name": "tasks_input",
                    "label": "Tasks",
                    "type": "json",
                    "default": "={{$previous_node.output.tasks}}",
                    "description": (
                        "Array of {id, description, assignee_role} tasks — typically a "
                        "Task Planner's output."
                    ),
                },
                {
                    "name": "persona_map",
                    "label": "Role → Persona",
                    "type": "key-value",
                    "default": {},
                    "description": "Map each task role to the persona id that handles it.",
                },
                {
                    "name": "default_persona_id",
                    "label": "Fallback Persona",
                    "type": "persona-picker",
                    "required": False,
                    "description": "Used when a task's role isn't in the map.",
                },
                {
                    "name": "max_concurrent",
                    "label": "Max Concurrent",
                    "type": "number",
                    "default": 4,
                    "mode": "advanced",
                },
                {
                    "name": "shared_context",
                    "label": "Shared Context",
                    "type": "string",
                    "mode": "advanced",
                    "description": "Prepended to every task's user message.",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "results", "type": "array"},
                {"label": "success_count", "type": "number"},
                {"label": "failure_count", "type": "number"},
            ],
            allow_error=True,
        )

    def _parse_tasks(self, input_data: dict[str, Any]) -> list[dict[str, Any]]:
        raw = self.props.tasks_input
        if isinstance(raw, str):
            raw = raw.strip()
            if not raw:
                raw = None
            else:
                try:
                    raw = json.loads(raw)
                except json.JSONDecodeError:
                    raw = None
        if not raw:
            raw = input_data.get("tasks") or []
        if not isinstance(raw, list):
            return []
        return [t for t in raw if isinstance(t, dict) and t.get("description")]

    def _parse_persona_map(self) -> dict[str, str]:
        raw = self.props.persona_map
        if isinstance(raw, str):
            try:
                raw = json.loads(raw) if raw.strip() else {}
            except json.JSONDecodeError:
                return {}
        return {str(k): str(v) for k, v in (raw or {}).items() if v}

    async def _run_one_task(
        self,
        task: dict[str, Any],
        persona_id: str | None,
        context: NodeContext,
        sem: asyncio.Semaphore,
    ) -> dict[str, Any]:
        from apps.api.app.node_system.nodes.ai.agent.agent import AgentNode

        async with sem:
            props: dict[str, Any] = {}
            if persona_id:
                props["persona_id"] = persona_id
            user_content = task.get("description", "")
            if self.props.shared_context:
                user_content = f"{self.props.shared_context}\n\n{user_content}"
            props["messages"] = [{"role": "user", "content": user_content}]

            agent = AgentNode(node_id=f"{self.node_id}.{task.get('id', 'task')}", properties=props)
            try:
                result = await agent.execute({}, context)
            except Exception as e:
                logger.warning("parallel task %s crashed: %s", task.get("id"), e)
                return {
                    "task_id": task.get("id"),
                    "success": False,
                    "error": str(e),
                }
            output = result.output_data or {}
            return {
                "task_id": task.get("id"),
                "assignee_role": task.get("assignee_role"),
                "success": result.success,
                "error": result.error,
                "output": output.get("content"),
                "tokens": output.get("tokens"),
                "agent_usage": output.get("agent_usage"),
            }

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        tasks = self._parse_tasks(input_data)
        if not tasks:
            return NodeResult(success=False, error="No tasks to fan out.")

        persona_map = self._parse_persona_map()
        fallback = self.props.default_persona_id

        # Validate persona ids parse — silently drop invalid ones.
        def _valid(pid: str | None) -> str | None:
            if not pid:
                return None
            try:
                _uuid.UUID(pid)
                return pid
            except (ValueError, TypeError):
                return None

        sem = asyncio.Semaphore(max(int(self.props.max_concurrent or 1), 1))

        coros = []
        for t in tasks:
            role = t.get("assignee_role") or ""
            persona_id = _valid(persona_map.get(role)) or _valid(fallback)
            coros.append(self._run_one_task(t, persona_id, context, sem))

        results = await asyncio.gather(*coros)
        success_count = sum(1 for r in results if r.get("success"))

        return NodeResult(
            success=True,
            output_data={
                "results": results,
                "success_count": success_count,
                "failure_count": len(results) - success_count,
            },
        )
