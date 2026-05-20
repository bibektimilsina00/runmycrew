from __future__ import annotations

import asyncio
import json
from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

_MAX_ITERATIONS = 1000


class LoopProperties(BaseModel):
    loop_type: str = "for_each"
    # for_each
    items: Any = Field(default_factory=list)
    # for
    count: int = 10
    start: int = 0
    step: int = 1
    # while / do_while
    condition: str = "{{variables.shouldContinue}}"
    max_iterations: int = 100
    # shared
    parallel: bool = False


class LoopNode(BaseNode[LoopProperties]):
    @classmethod
    def get_properties_model(cls) -> type[LoopProperties]:
        return LoopProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="logic.loop",
            name="Loop",
            category="logic",
            description="Execute nodes in a loop. Choose from For Each, For, While, or Do While.",
            icon="Repeat2",
            color="#3b82f6",
            default_width=400,
            default_height=280,
            properties=[
                {
                    "name": "loop_type",
                    "label": "Loop Type",
                    "type": "options",
                    "default": "for_each",
                    "options": [
                        {"label": "For Each — iterate over array items", "value": "for_each"},
                        {"label": "For — fixed number of iterations", "value": "for"},
                        {"label": "While — run while condition is true", "value": "while"},
                        {"label": "Do While — run at least once, then check condition", "value": "do_while"},
                    ],
                },
                # For Each
                {
                    "name": "items",
                    "label": "Items",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{trigger.output.items}}",
                    "description": "Array to iterate. Use {{loop.item}}, {{loop.index}}, {{loop.total}} in downstream nodes.",
                    "condition": {"field": "loop_type", "value": "for_each"},
                },
                # For
                {
                    "name": "count",
                    "label": "Count",
                    "type": "number",
                    "default": 10,
                    "required": True,
                    "description": "Number of iterations. Use {{loop.value}}, {{loop.index}}, {{loop.total}} in downstream nodes.",
                    "condition": {"field": "loop_type", "value": "for"},
                },
                {
                    "name": "start",
                    "label": "Start",
                    "type": "number",
                    "default": 0,
                    "mode": "advanced",
                    "condition": {"field": "loop_type", "value": "for"},
                },
                {
                    "name": "step",
                    "label": "Step",
                    "type": "number",
                    "default": 1,
                    "mode": "advanced",
                    "condition": {"field": "loop_type", "value": "for"},
                },
                # While / Do While
                {
                    "name": "condition",
                    "label": "Condition",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{variables.hasMore}}",
                    "description": "Loop continues while this is truthy. Use {{loop.iteration}} in downstream nodes.",
                    "condition": {"field": "loop_type", "value": ["while", "do_while"]},
                },
                {
                    "name": "max_iterations",
                    "label": "Max Iterations",
                    "type": "number",
                    "default": 100,
                    "mode": "advanced",
                    "description": "Safety cap to prevent infinite loops.",
                    "condition": {"field": "loop_type", "value": ["while", "do_while"]},
                },
                # Shared
                {
                    "name": "parallel",
                    "label": "Run in parallel",
                    "type": "boolean",
                    "default": False,
                    "mode": "advanced",
                    "description": "Execute all iterations concurrently (For Each / For only).",
                    "condition": {"field": "loop_type", "value": ["for_each", "for"]},
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "results", "type": "array"},
                {"label": "count", "type": "number"},
                {"label": "iterations", "type": "number"},
            ],
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.run_downstream is None:
            return NodeResult(success=False, error="run_downstream not available")

        lt = self.props.loop_type

        if lt == "for_each":
            return await self._run_for_each(input_data, context)
        elif lt == "for":
            return await self._run_for(input_data, context)
        elif lt == "while":
            return await self._run_while(input_data, context)
        elif lt == "do_while":
            return await self._run_do_while(input_data, context)
        else:
            return NodeResult(success=False, error=f"Unknown loop_type: {lt}")

    # ── For Each ──────────────────────────────────────────────────────────────

    async def _run_for_each(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        raw = self.props.items
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                return NodeResult(success=False, error=f"items must be an array, got: {raw!r}")
        if not isinstance(raw, list):
            return NodeResult(success=False, error=f"items must be an array, got {type(raw).__name__}")

        items = raw[:_MAX_ITERATIONS]
        total = len(items)
        if total == 0:
            return NodeResult(success=True, output_data={"results": [], "count": 0}, handled_successors=True)

        async def run_item(i: int, item: Any) -> dict[str, Any]:
            loop_vars = {"item": item, "index": i, "total": total, "items": items}
            sub = await context.run_downstream(loop_vars, loop_data=loop_vars)
            return sub[0] if sub else {}

        if self.props.parallel:
            results = list(await asyncio.gather(*[run_item(i, it) for i, it in enumerate(items)]))
        else:
            results = [await run_item(i, it) for i, it in enumerate(items)]

        return NodeResult(success=True, output_data={"results": results, "count": total}, handled_successors=True)

    # ── For ───────────────────────────────────────────────────────────────────

    async def _run_for(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        count = max(0, min(self.props.count, _MAX_ITERATIONS))
        start = self.props.start
        step = self.props.step if self.props.step != 0 else 1
        values = [start + i * step for i in range(count)]
        total = len(values)

        if total == 0:
            return NodeResult(success=True, output_data={"results": [], "count": 0}, handled_successors=True)

        async def run_iter(i: int, value: int) -> dict[str, Any]:
            loop_vars = {"index": i, "value": value, "total": total}
            sub = await context.run_downstream(loop_vars, loop_data=loop_vars)
            return sub[0] if sub else {}

        if self.props.parallel:
            results = list(await asyncio.gather(*[run_iter(i, v) for i, v in enumerate(values)]))
        else:
            results = [await run_iter(i, v) for i, v in enumerate(values)]

        return NodeResult(success=True, output_data={"results": results, "count": total}, handled_successors=True)

    # ── While ─────────────────────────────────────────────────────────────────

    async def _run_while(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        from apps.api.app.execution_engine.engine.template_resolver import TemplateResolver

        max_iter = max(1, min(self.props.max_iterations, _MAX_ITERATIONS))
        results: list[dict[str, Any]] = []
        current_input = input_data
        iteration = 0

        while iteration < max_iter:
            resolver = TemplateResolver(
                node_outputs={}, trigger_data=current_input, variables={}
            )
            if not resolver.evaluate_condition(self.props.condition):
                break

            loop_vars = {"iteration": iteration, "total": max_iter}
            sub = await context.run_downstream({**current_input, "iteration": iteration}, loop_data=loop_vars)
            iteration_result = sub[0] if sub else {}
            results.append(iteration_result)
            current_input = iteration_result
            iteration += 1

        return NodeResult(success=True, output_data={"results": results, "iterations": iteration}, handled_successors=True)

    # ── Do While ─────────────────────────────────────────────────────────────

    async def _run_do_while(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        from apps.api.app.execution_engine.engine.template_resolver import TemplateResolver

        max_iter = max(1, min(self.props.max_iterations, _MAX_ITERATIONS))
        results: list[dict[str, Any]] = []
        current_input = input_data
        iteration = 0

        while iteration < max_iter:
            loop_vars = {"iteration": iteration, "total": max_iter}
            sub = await context.run_downstream({**current_input, "iteration": iteration}, loop_data=loop_vars)
            iteration_result = sub[0] if sub else {}
            results.append(iteration_result)
            current_input = iteration_result
            iteration += 1

            resolver = TemplateResolver(
                node_outputs={}, trigger_data=current_input, variables={}
            )
            if not resolver.evaluate_condition(self.props.condition):
                break

        return NodeResult(success=True, output_data={"results": results, "iterations": iteration}, handled_successors=True)
