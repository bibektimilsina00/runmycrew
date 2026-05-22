from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)


class SubWorkflowProperties(BaseModel):
    workflow_id: str = ""
    input_data: Any = None


class SubWorkflowNode(BaseNode[SubWorkflowProperties]):
    @classmethod
    def get_properties_model(cls) -> type[SubWorkflowProperties]:
        return SubWorkflowProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="logic.sub_workflow",
            name="Sub-Workflow",
            category="logic",
            description="Run another workflow and use its output as input to the next node.",
            icon="GitBranch",
            color="#8b5cf6",
            properties=[
                {
                    "name": "workflow_id",
                    "label": "Workflow ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "UUID of the workflow to call",
                    "description": "The ID of the workflow to execute. Find it in the workflow URL.",
                },
                {
                    "name": "input_data",
                    "label": "Extra Input (JSON)",
                    "type": "json",
                    "required": False,
                    "description": "Optional extra fields merged into the trigger data passed to the sub-workflow.",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "sub_workflow_output", "type": "object"},
                {"label": "workflow_id", "type": "string"},
            ],
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        workflow_id = (self.props.workflow_id or "").strip()
        if not workflow_id:
            return NodeResult(success=False, error="workflow_id is required")

        try:
            uuid.UUID(workflow_id)
        except ValueError:
            return NodeResult(success=False, error=f"Invalid workflow_id: {workflow_id!r}")

        extra_input = self.props.input_data or {}
        if isinstance(extra_input, str):
            import json
            try:
                extra_input = json.loads(extra_input)
            except Exception:
                extra_input = {}

        try:
            from apps.api.app.core.database import AsyncSessionLocal
            from apps.api.app.execution_engine.engine.workflow_runner import WorkflowRunner
            from apps.api.app.repositories.workflow_repository import WorkflowRepository

            async with AsyncSessionLocal() as db:
                repo = WorkflowRepository(db)
                workflow = await repo.get_by_id(uuid.UUID(workflow_id))
                if not workflow:
                    return NodeResult(success=False, error=f"Workflow {workflow_id} not found")

                sub_input = {**input_data, **extra_input}
                sub_execution_id = f"{context.execution_id}-sub-{workflow_id[:8]}"

                runner = WorkflowRunner(
                    workflow_id=str(workflow.id),
                    execution_id=sub_execution_id,
                    graph=workflow.graph,
                    db=db,
                    credentials=context.credentials,
                    emitter=context.emitter,
                )
                output = await runner.run(sub_input)

            return NodeResult(
                success=True,
                output_data={"sub_workflow_output": output, "workflow_id": workflow_id},
            )
        except Exception as e:
            logger.error(f"SubWorkflowNode failed for workflow {workflow_id}: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))
