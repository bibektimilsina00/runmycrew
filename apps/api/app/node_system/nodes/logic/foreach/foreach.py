from __future__ import annotations

import asyncio
import json
from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

_MAX_ITERATIONS = 1000


class ForEachProperties(BaseModel):
    items: Any = Field(default_factory=list)
    parallel: bool = False


class ForEachNode(BaseNode[ForEachProperties]):
    @classmethod
    def get_properties_model(cls) -> type[ForEachProperties]:
        return ForEachProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="logic.foreach",
            name="For Each",
            category="logic",
            description="Execute downstream nodes once per item in an array.",
            icon="Repeat",
            color="#6366f1",
            properties=[
                {
                    "name": "items",
                    "label": "Items",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{trigger.output.items}}",
                    "description": "Array to iterate. Each item is passed downstream as {item, index, total}.",
                },
                {
                    "name": "parallel",
                    "label": "Run in parallel",
                    "type": "boolean",
                    "default": False,
                    "mode": "advanced",
                    "description": "Execute all iterations concurrently (max 1000 items).",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "results", "type": "array"},
                {"label": "count", "type": "number"},
            ],
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        raw = self.props.items

        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                return NodeResult(success=False, error=f"items must be an array, got: {raw!r}")

        if not isinstance(raw, list):
            return NodeResult(success=False, error=f"items must be an array, got {type(raw).__name__}")

        items = raw[:_MAX_ITERATIONS]
        total = len(items)

        if total == 0:
            return NodeResult(
                success=True,
                output_data={"results": [], "count": 0},
                handled_successors=True,
            )

        if context.run_downstream is None:
            return NodeResult(success=False, error="run_downstream not injected — cannot iterate")

        async def run_item(i: int, item: Any) -> dict[str, Any]:
            sub_results = await context.run_downstream({"item": item, "index": i, "total": total})
            return sub_results[0] if sub_results else {}

        if self.props.parallel:
            results = list(await asyncio.gather(*[run_item(i, it) for i, it in enumerate(items)]))
        else:
            results = [await run_item(i, it) for i, it in enumerate(items)]

        return NodeResult(
            success=True,
            output_data={"results": results, "count": total},
            handled_successors=True,
        )
