from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

_MAX_ITERATIONS = 1000


class ForLoopProperties(BaseModel):
    count: int = 10
    start: int = 0
    step: int = 1
    parallel: bool = False


class ForLoopNode(BaseNode[ForLoopProperties]):
    @classmethod
    def get_properties_model(cls) -> type[ForLoopProperties]:
        return ForLoopProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="logic.for",
            name="For Loop",
            category="logic",
            description="Execute downstream nodes a fixed number of times with a counter.",
            icon="Hash",
            color="#6366f1",
            properties=[
                {"name": "count", "label": "Count", "type": "number", "required": True, "default": 10, "description": "Number of iterations."},
                {"name": "start", "label": "Start", "type": "number", "default": 0, "mode": "advanced"},
                {"name": "step", "label": "Step", "type": "number", "default": 1, "mode": "advanced"},
                {"name": "parallel", "label": "Run in parallel", "type": "boolean", "default": False, "mode": "advanced"},
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "results", "type": "array"},
                {"label": "count", "type": "number"},
            ],
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.run_downstream is None:
            return NodeResult(success=False, error="run_downstream not injected")

        count = max(0, min(self.props.count, _MAX_ITERATIONS))
        start = self.props.start
        step = self.props.step if self.props.step != 0 else 1

        values = [start + i * step for i in range(count)]
        total = len(values)

        if total == 0:
            return NodeResult(success=True, output_data={"results": [], "count": 0}, handled_successors=True)

        import asyncio

        async def run_iteration(i: int, value: int) -> dict[str, Any]:
            loop_vars = {"index": i, "value": value, "total": total}
            sub = await context.run_downstream(loop_vars, loop_data=loop_vars)
            return sub[0] if sub else {}

        if self.props.parallel:
            results = list(await asyncio.gather(*[run_iteration(i, v) for i, v in enumerate(values)]))
        else:
            results = [await run_iteration(i, v) for i, v in enumerate(values)]

        return NodeResult(
            success=True,
            output_data={"results": results, "count": total},
            handled_successors=True,
        )
