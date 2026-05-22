from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.logger import get_logger
from apps.api.app.execution_engine.engine.node_executor import node_executor
from apps.api.app.node_system.base.node_context import NodeContext

logger = get_logger(__name__)


class PauseSignal(Exception):
    """Raised by a node to pause execution at this point."""

    def __init__(self, node_id: str, resume_schema: dict[str, Any]):
        self.node_id = node_id
        self.resume_schema = resume_schema
        super().__init__(f"Execution paused at node {node_id}")


class CancelledException(Exception):
    """Raised when a cancellation signal is detected in Redis."""
    pass


class WorkflowRunner:
    def __init__(
        self,
        workflow_id: str,
        execution_id: str,
        graph: dict[str, Any],
        db: AsyncSession | None = None,
        on_log: Any = None,
        credentials: list[dict[str, Any]] | None = None,
        emitter: Any = None,
    ):
        self.workflow_id = workflow_id
        self.execution_id = execution_id
        self.graph = graph
        self.nodes = {node["id"]: node for node in graph.get("nodes", [])}
        self.edges = graph.get("edges", [])
        self.credentials = credentials or []
        self.db = db
        self.on_log = on_log
        self.emitter = emitter
        self.variables: dict[str, Any] = {}
        self.env: dict[str, str] = {}
        self.secrets: dict[str, str] = {}
        self.loop_data: dict[str, Any] = {}  # populated by loop nodes for {{loop.*}}

        # Parallel-safe shared state
        self._lock = asyncio.Lock()
        self._executed: dict[str, Any] = {}   # node_id → NodeResult
        self._outputs: dict[str, dict[str, Any]] = {}  # node_id → output_data
        self._failed = asyncio.Event()
        self._error_message: str | None = None

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def run(self, trigger_data: dict[str, Any]) -> dict[str, Any]:
        self._trigger_data = trigger_data
        logger.info(f"Starting workflow execution {self.execution_id}")

        start_nodes = self._get_start_nodes()
        if not start_nodes:
            logger.info(f"Workflow {self.workflow_id} has no nodes — completing immediately")
            return {}

        try:
            await asyncio.gather(
                *[self._execute_node(n, trigger_data) for n in start_nodes]
            )
        except PauseSignal:
            raise  # propagate to Celery task
        except CancelledException:
            raise  # propagate to Celery task
        except Exception as e:
            self._failed.set()
            self._error_message = str(e)

        if self._failed.is_set():
            raise Exception(self._error_message or "Execution failed")

        if self._outputs:
            last_node_id = list(self._outputs.keys())[-1]
            return self._outputs[last_node_id]
        return {}

    # ------------------------------------------------------------------
    # Internal: run a single node then dispatch its successors
    # ------------------------------------------------------------------

    async def _is_cancelled(self) -> bool:
        try:
            from apps.api.app.core.redis import get_redis
            redis = await get_redis()
            result = await redis.get(f"execution:cancel:{self.execution_id}")
            return result is not None
        except Exception:
            return False

    async def _execute_node(self, node_id: str, input_data: dict[str, Any]) -> None:
        if self._failed.is_set():
            return

        if await self._is_cancelled():
            logger.info(f"Execution {self.execution_id} cancelled before node {node_id}")
            raise CancelledException(f"Execution cancelled at node {node_id}")

        node_data = self.nodes.get(node_id)

        # Dedup: only one coroutine may execute a given node (pinned nodes bypass dedup)
        is_pinned = node_data and node_data.get("data", {}).get("pinned", False)
        async with self._lock:
            if node_id in self._executed and not is_pinned:
                return
            self._executed[node_id] = None  # placeholder while running
        if not node_data:
            logger.warning(f"Node {node_id} not found in graph, skipping")
            return

        label = node_data.get("data", {}).get("label") or node_data["type"]
        await self._log(label, node_id=node_id)

        from apps.api.app.execution_engine.engine.template_resolver import TemplateResolver
        resolver = TemplateResolver(
            node_outputs=self._outputs,
            trigger_data=self._trigger_data,
            variables=self.variables,
            env=self.env,
            secrets=self.secrets,
            loop_data=self.loop_data,
        )
        resolved_properties = resolver.resolve_properties(
            node_data.get("data", {}).get("properties", {})
        )

        from apps.api.app.core.http import get_http_client
        http_client = await get_http_client()

        # Build run_downstream callback for nodes that handle their own successors (e.g. ForEach).
        # Pre-bind the successor node IDs for this specific node.
        _successor_ids = [
            e["target"] for e in self.edges
            if e["source"] == node_id and e.get("sourceHandle") != "error"
        ]

        async def run_downstream(
            item_input: dict[str, Any],
            loop_data: dict[str, Any] | None = None,
        ) -> list[dict[str, Any]]:
            results: list[dict[str, Any]] = []
            for start_id in _successor_ids:
                sub_runner = WorkflowRunner(
                    workflow_id=self.workflow_id,
                    execution_id=self.execution_id,
                    graph=self.graph,
                    db=self.db,
                    on_log=self.on_log,
                    credentials=self.credentials,
                    emitter=self.emitter,
                )
                sub_runner.variables = self.variables
                sub_runner.env = self.env
                sub_runner.secrets = self.secrets
                sub_runner.loop_data = loop_data or item_input  # expose as {{loop.*}}
                sub_runner._outputs = dict(self._outputs)
                result = await sub_runner._execute_subgraph(start_id, item_input)
                results.append(result)
                async with self._lock:
                    self._outputs.update(sub_runner._outputs)
            return results

        # Build pause callback
        async def pause_execution(resume_schema: dict[str, Any]) -> None:
            raise PauseSignal(node_id, resume_schema)

        context = NodeContext(
            execution_id=self.execution_id,
            workflow_id=self.workflow_id,
            node_id=node_id,
            variables=self.variables,
            credentials=self.credentials,
            http_client=http_client,
            db=self.db,
            emitter=self.emitter,
            run_downstream=run_downstream,
            pause=pause_execution,
        )

        await self._emit("node_started", {
            "node_id": node_id,
            "node_type": node_data.get("type"),
            "label": label,
        })

        # Retry config — read from resolved properties
        max_retries = int(resolved_properties.get("retries") or 0)
        retry_delay_ms = int(resolved_properties.get("retry_delay_ms") or 1000)
        attempt = 0
        result = None

        while True:
            result = await node_executor.execute_node(
                node_type=node_data["type"],
                node_id=node_id,
                properties=resolved_properties,
                input_data=input_data,
                context=context,
            )
            if result.success or attempt >= max_retries:
                break
            attempt += 1
            await self._log(
                f"Attempt {attempt}/{max_retries} failed: {result.error}. Retrying in {retry_delay_ms}ms…",
                level="warning",
                node_id=node_id,
            )
            await asyncio.sleep(retry_delay_ms / 1000)

        async with self._lock:
            self._executed[node_id] = result

        for log_msg in result.logs:
            await self._log(log_msg, level="info" if result.success else "error", node_id=node_id)

        next_edges = [e for e in self.edges if e["source"] == node_id]

        if result.success:
            async with self._lock:
                self._outputs[node_id] = result.output_data

            await self._emit("node_completed", {"node_id": node_id, "output": result.output_data})
            await self._log(label, node_id=node_id, payload={
                "input": resolved_properties,
                "data_in": input_data,
                "output": result.output_data,
            })

            # If node handled its own successors, don't dispatch edges
            if result.handled_successors:
                return

            branch = result.output_data.get("branch")
            active_edges = [
                e for e in next_edges
                if e.get("sourceHandle") != "error"
                and not (branch and e.get("sourceHandle") and e.get("sourceHandle") != branch)
            ]

            if active_edges:
                await asyncio.gather(*[
                    self._execute_node(e["target"], result.output_data)
                    for e in active_edges
                ])

        else:
            await self._emit("node_failed", {"node_id": node_id, "error": result.error})
            await self._log(label, level="error", node_id=node_id, payload={
                "input": resolved_properties,
                "data_in": input_data,
                "error": result.error,
            })

            error_edges = [e for e in next_edges if e.get("sourceHandle") == "error"]
            if error_edges:
                error_payload = {"input": resolved_properties, "data_in": input_data, "error": result.error}
                await asyncio.gather(*[
                    self._execute_node(e["target"], error_payload)
                    for e in error_edges
                ])
            else:
                self._failed.set()
                error = result.error or "Unknown error"
                self._error_message = error if "Node" in error else f"Node {label} failed: {error}"
                logger.error(f"Execution failed at node {node_id}: {result.error}")

    async def _resume_from(self, paused_node_id: str, resume_input: dict[str, Any]) -> dict[str, Any]:
        """Resume execution after a pause, injecting resume_input as the paused node's output."""
        # Treat paused node as completed with resume_input as its output
        async with self._lock:
            self._executed[paused_node_id] = True
            self._outputs[paused_node_id] = resume_input

        # Follow outgoing edges from the paused node
        next_edges = [e for e in self.edges if e["source"] == paused_node_id]
        if next_edges:
            await asyncio.gather(*[
                self._execute_node(e["target"], resume_input)
                for e in next_edges
            ])

        if self._failed.is_set():
            raise Exception(self._error_message or "Execution failed")

        if self._outputs:
            return self._outputs[list(self._outputs.keys())[-1]]
        return {}

    async def _execute_subgraph(self, start_node_id: str, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a sub-graph starting from start_node_id. Used by ForEach."""
        await self._execute_node(start_node_id, input_data)
        if start_node_id in self._outputs:
            return self._outputs[start_node_id]
        return {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_start_nodes(self) -> list[str]:
        target_nodes = {e["target"] for e in self.edges}
        return [n for n in self.nodes if n not in target_nodes]

    async def _emit(self, event_type: str, data: dict[str, Any]) -> None:
        if self.emitter:
            await self.emitter.emit(event_type, data)

    async def _log(
        self, message: str, level: str = "info", node_id: str | None = None, payload: Any = None
    ) -> None:
        if self.on_log:
            await self.on_log(message, level=level, node_id=node_id, payload=payload)
