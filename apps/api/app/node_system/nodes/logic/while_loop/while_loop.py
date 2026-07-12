from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

_MAX_ITERATIONS = 1000


class WhileLoopProperties(BaseModel):
    condition: str = "{{$step.shouldContinue}}"
    maxIterations: int = 100


class WhileLoopNode(BaseNode[WhileLoopProperties]):
    @classmethod
    def get_properties_model(cls) -> type[WhileLoopProperties]:
        return WhileLoopProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="logic.while",
            name="While Loop",
            category="logic",
            description="Execute downstream nodes repeatedly while a condition is true.",
            icon="RefreshCw",
            color="#6366f1",
            properties=[
                {
                    "name": "condition",
                    "label": "Condition",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{$step.hasMore}}",
                    "description": "Template expression. Loop continues while this resolves to truthy. Supports: {{$step.field}} == value, {{$step.field}} < 10, {{$step.field}} != null",
                },
                {
                    "name": "maxIterations",
                    "label": "Max Iterations",
                    "type": "number",
                    "default": 100,
                    "mode": "advanced",
                    "description": "Safety cap to prevent infinite loops.",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "results", "type": "array"},
                {"label": "iterations", "type": "number"},
            ],
        )

    @classmethod
    def deferred_properties(cls) -> frozenset[str]:
        # Re-evaluated every iteration; the runner must not pre-resolve it.
        return frozenset({"condition"})

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.run_downstream is None:
            return NodeResult(success=False, error="run_downstream not injected")

        from apps.api.app.execution_engine.engine.template_resolver import TemplateResolver

        max_iter = max(1, min(self.props.maxIterations, _MAX_ITERATIONS))
        results: list[dict[str, Any]] = []
        current_input = input_data
        iteration = 0

        while iteration < max_iter:
            resolver = TemplateResolver.for_iteration(
                current_input,
                variables=context.variables,
                env=getattr(context, "env", {}),
            )

            if not resolver.evaluate_condition(self.props.condition):
                break

            loop_vars = {"iteration": iteration, "total": self.props.maxIterations}
            sub = await context.run_downstream(
                {**current_input, "iteration": iteration}, loop_data=loop_vars
            )
            iteration_result = sub[0] if sub else {}
            results.append(iteration_result)
            current_input = iteration_result
            iteration += 1

        return NodeResult(
            success=True,
            output_data={"results": results, "iterations": iteration},
            handled_successors=True,
        )
