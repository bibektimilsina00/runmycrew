from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

_MAX_ITERATIONS = 1000


class DoWhileProperties(BaseModel):
    condition: str = "{{variables.shouldContinue}}"
    maxIterations: int = 100


class DoWhileNode(BaseNode[DoWhileProperties]):
    @classmethod
    def get_properties_model(cls) -> type[DoWhileProperties]:
        return DoWhileProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="logic.do_while",
            name="Do While",
            category="logic",
            description="Execute downstream nodes at least once, then repeat while condition is true.",
            icon="RotateCw",
            color="#6366f1",
            properties=[
                {
                    "name": "condition",
                    "label": "Condition",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{variables.hasMore}}",
                    "description": "Checked AFTER each iteration. Same syntax as While Loop.",
                },
                {
                    "name": "maxIterations",
                    "label": "Max Iterations",
                    "type": "number",
                    "default": 100,
                    "mode": "advanced",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "results", "type": "array"},
                {"label": "iterations", "type": "number"},
            ],
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.run_downstream is None:
            return NodeResult(success=False, error="run_downstream not injected")

        from apps.api.app.execution_engine.engine.template_resolver import TemplateResolver

        max_iter = max(1, min(self.props.maxIterations, _MAX_ITERATIONS))
        results: list[dict[str, Any]] = []
        current_input = input_data
        iteration = 0

        while iteration < max_iter:
            loop_vars = {"iteration": iteration, "total": max_iter}
            sub = await context.run_downstream(
                {**current_input, "iteration": iteration}, loop_data=loop_vars
            )
            iteration_result = sub[0] if sub else {}
            results.append(iteration_result)
            current_input = iteration_result
            iteration += 1

            # Condition checked AFTER execution
            resolver = TemplateResolver(
                node_outputs={"iteration": current_input},
                trigger_data=current_input,
                variables=context.variables,
                env=getattr(context, "env", {}),
            )
            if not resolver.evaluate_condition(self.props.condition):
                break

        return NodeResult(
            success=True,
            output_data={"results": results, "iterations": iteration},
            handled_successors=True,
        )
