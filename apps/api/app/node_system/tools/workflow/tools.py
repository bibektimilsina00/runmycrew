from __future__ import annotations

from typing import Any

from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.tools.base import ToolDefinition, ToolParam, ToolResult
from apps.api.app.node_system.tools.registry import tool_registry


async def _execute_workflow(params: dict[str, Any], context: NodeContext) -> ToolResult:
    workflow_id = params.get('workflowId')
    if not workflow_id:
        return ToolResult(success=False, error="workflowId is required")
    if not context.db:
        return ToolResult(success=False, error="Database context required for workflow execution")

    try:
        from apps.api.app.execution_engine.engine.workflow_runner import WorkflowRunner
        from apps.api.app.repositories.workflow_repository import WorkflowRepository

        repo = WorkflowRepository(context.db)
        workflow = await repo.get_by_id(workflow_id)
        if not workflow:
            return ToolResult(success=False, error=f"Workflow {workflow_id} not found")

        graph = workflow.graph or {}
        runner = WorkflowRunner(
            workflow_id=workflow_id,
            execution_id=context.execution_id,
            graph=graph,
            db=context.db,
            credentials=context.credentials,
        )

        trigger_data = {k: v for k, v in params.items() if k != 'workflowId'}
        result = await runner.run(trigger_data)
        return ToolResult(success=True, output=result)
    except Exception as e:
        return ToolResult(success=False, error=str(e))


tool_registry.register(
    ToolDefinition(
        id='workflow_executor',
        name='Run Workflow',
        description='Execute another workflow as a tool',
        params={
            'workflowId': ToolParam(
                type='string',
                required=True,
                visibility='user-only',
                description='ID of the workflow to run',
            ),
            'input': ToolParam(
                type='json',
                visibility='user-or-llm',
                description='Input data for the workflow',
            ),
        },
    ),
    _execute_workflow,
)
