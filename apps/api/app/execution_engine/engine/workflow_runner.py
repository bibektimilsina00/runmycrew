from __future__ import annotations

import asyncio
import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.logger import get_logger
from apps.api.app.execution_engine.engine.node_executor import node_executor
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_item import NodeItem, PairedItem

logger = get_logger(__name__)

# Bound total work so a cyclic graph or runaway loop fails fast instead of
# hanging the worker (guards against accidental or malicious infinite loops).
_MAX_NODE_EXECUTIONS = 10_000
_MAX_SUBGRAPH_DEPTH = 50


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
        workspace_id: str | None = None,
        _depth: int = 0,
        _budget: dict[str, int] | None = None,
    ):
        self.workflow_id = workflow_id
        self.execution_id = execution_id
        self.graph = graph
        self.nodes = {node["id"]: node for node in graph.get("nodes", [])}
        self.edges = graph.get("edges", [])
        self.credentials = credentials or []
        self.db = db
        # Carried through to every NodeContext so polling triggers can
        # persist cursors against the correct workspace row. Optional —
        # synthetic test runs that don't supply it gracefully fall back
        # to stateless preview mode inside the trigger.
        self.workspace_id = workspace_id
        self.on_log = on_log
        self.emitter = emitter
        self.variables: dict[str, Any] = {}
        self.env: dict[str, str] = {}
        self.secrets: dict[str, str] = {}
        self.loop_data: dict[str, Any] = {}  # populated by loop nodes for {{loop.*}}
        # Trigger payload for {{$trigger.*}} bindings. run() overwrites it;
        # initialized here because sub-runners built by run_downstream call
        # _execute_subgraph directly and never pass through run().
        self._trigger_data: dict[str, Any] = {}

        # Parallel-safe shared state
        self._lock = asyncio.Lock()
        self._executed: dict[str, Any] = {}  # node_id → NodeResult
        self._outputs: dict[str, dict[str, Any]] = {}  # node_id → output_data
        # Rich per-item view kept in parallel with `_outputs`. Foundation for
        # the JSONata resolver's paired-item walking (PR4 wires it). Today
        # nothing reads from this map; it's populated as nodes complete so
        # the data is ready when PR4 lights up the resolver.
        self._output_items: dict[str, list[NodeItem]] = {}
        # Every artifact any node emitted during this run (explicit or
        # detected). Accumulated so the terminal task can attach the full
        # list to the assistant message even if the SSE stream disconnected.
        self._collected_artifacts: list = []
        self._failed = asyncio.Event()
        self._error_message: str | None = None
        self._depth = _depth
        # Shared across sub-runners so the whole run draws from one budget.
        self._budget = _budget if _budget is not None else {"remaining": _MAX_NODE_EXECUTIONS}

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def _acquire_concurrency(self) -> tuple[Any, Any]:
        """Acquire the workflow-level concurrency mutex.

        Returns ``(manager, acquire_result)`` so the caller can
        release on exit. When the workflow is a sub-runner (depth>0)
        we skip the mutex entirely — sub-workflows are part of the
        parent's run by definition. Loads policy from the workflow
        row; falls back to ``skip`` + 60s queue wait if the row was
        deleted between trigger and run.
        """
        if self._depth > 0 or self.db is None:
            return None, None
        try:
            import uuid as _uuid

            from apps.api.app.execution_engine.concurrency import (
                ConcurrencyManager,
                ConcurrencyPolicy,
            )
            from apps.api.app.features.workflows.models import Workflow

            try:
                wf_uuid = _uuid.UUID(str(self.workflow_id))
            except (ValueError, TypeError):
                return None, None
            wf = await self.db.get(Workflow, wf_uuid)
            if wf is None:
                return None, None
            try:
                policy = ConcurrencyPolicy(wf.concurrency_policy or "skip")
            except ValueError:
                policy = ConcurrencyPolicy.SKIP
            mgr = ConcurrencyManager()
            result = await mgr.acquire(
                wf.id,
                policy=policy,
                queue_max_wait_seconds=int(wf.concurrency_queue_max_wait_seconds or 60),
            )
            return mgr, result
        except Exception:
            # Concurrency MUST never break the run path. Log + fall
            # through to lock-free execution.
            logger.exception("concurrency: acquire failed; running lock-free")
            return None, None

    async def _release_concurrency(self, mgr: Any, result: Any) -> None:
        if mgr is None or result is None or not getattr(result, "token", None):
            return
        try:
            await mgr.release(self.workflow_id, result.token)
        except Exception:
            logger.exception("concurrency: release failed")

    async def run(self, trigger_data: dict[str, Any]) -> dict[str, Any]:
        # ── Concurrency mutex (Phase 2 wiring) ─────────────────────
        # Acquire BEFORE we set any per-run state so that a skipped
        # fire returns immediately without touching DB / outputs.
        cc_mgr, cc_result = await self._acquire_concurrency()
        if cc_result is not None and not cc_result.acquired:
            logger.info(
                "workflow=%s execution=%s skipped — concurrency status=%s",
                self.workflow_id,
                self.execution_id,
                cc_result.status,
            )
            return {
                "_concurrency_status": cc_result.status,
                "_skipped": True,
            }

        self._trigger_data = trigger_data
        logger.info(f"Starting workflow execution {self.execution_id}")

        start_nodes = self._get_start_nodes()
        if not start_nodes:
            logger.info(f"Workflow {self.workflow_id} has no nodes — completing immediately")
            return {}

        # If the caller passed no trigger payload (manual Run from the
        # editor), replay each trigger start node's last captured fixture.
        # Lets the user iterate on downstream nodes without re-triggering
        # the external event each time. Falls back to `{}` per node so
        # `require_webhook_payload` still surfaces a clear error when
        # nothing has ever been captured.
        per_node_input: dict[str, dict[str, Any]] = {}
        if not trigger_data and self.db is not None:
            import uuid as _uuid

            from apps.api.app.features.triggers.repository import TriggerFixtureRepository

            try:
                wf_uuid = _uuid.UUID(str(self.workflow_id))
            except (ValueError, TypeError):
                wf_uuid = None
            if wf_uuid is not None:
                fixture_repo = TriggerFixtureRepository(self.db)
                for node_id in start_nodes:
                    node_type = str(self.nodes.get(node_id, {}).get("type") or "")
                    if not node_type.startswith("trigger."):
                        continue
                    fixture = await fixture_repo.get(wf_uuid, node_id)
                    if fixture and isinstance(fixture.payload, dict):
                        per_node_input[node_id] = fixture.payload

        try:
            try:
                await asyncio.gather(
                    *[
                        self._execute_node(n, per_node_input.get(n, trigger_data))
                        for n in start_nodes
                    ]
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
        finally:
            # Always release the mutex, even on PauseSignal or
            # CancelledException. PauseSignal is a special case:
            # technically the run is paused, not finished — but the
            # mutex is per FIRE, not per RESUME, so releasing here is
            # correct. Resume reacquires.
            await self._release_concurrency(cc_mgr, cc_result)

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

    async def _execute_node(
        self,
        node_id: str,
        input_data: dict[str, Any],
        *,
        _source_node_id: str | None = None,
        _source_item_index: int = 0,
    ) -> None:
        """Run ``node_id`` and dispatch its successors.

        ``_source_node_id`` / ``_source_item_index`` describe which upstream
        node-output item fed this invocation. They are recorded as the
        ``paired_item`` provenance on every item the current node produces
        whenever the node itself didn't set one explicitly.
        """
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

        self._budget["remaining"] -= 1
        if self._budget["remaining"] < 0:
            raise RuntimeError(
                f"Execution exceeded the maximum of {_MAX_NODE_EXECUTIONS} node runs "
                "(possible infinite loop)"
            )

        label = node_data.get("data", {}).get("label") or node_data["type"]
        await self._log(label, node_id=node_id)

        from apps.api.app.execution_engine.engine.expression_engine import JsonataResolver
        from apps.api.app.execution_engine.engine.property_resolver import resolve_properties
        from apps.api.app.execution_engine.engine.template_resolver import TemplateResolver

        # `jsonata_resolver` is created a few lines down — defer the binding
        # by assigning after construction so the template resolver picks it
        # up for inline `{{ $step.x }}` lookups inside mixed-text fields.
        template_resolver = TemplateResolver(
            node_outputs=self._outputs,
            trigger_data=self._trigger_data,
            variables=self.variables,
            env=self.env,
            secrets=self.secrets,
            loop_data=self.loop_data,
        )
        # Label→id snapshot for `$node('Label')` lookups. On duplicate labels
        # the later-defined node wins (editor-side uniqueness lands in PR9).
        # Falls back to the raw node id so `$node('http_request-1')` works too.
        label_to_id: dict[str, str] = {}
        for nid, ndata in self.nodes.items():
            label_to_id[ndata.get("data", {}).get("label") or nid] = nid
            label_to_id.setdefault(nid, nid)
        incoming = (
            PairedItem(source_node_id=_source_node_id, source_item_index=_source_item_index)
            if _source_node_id is not None
            else None
        )
        jsonata_resolver = JsonataResolver(
            context=input_data,
            current_node_id=node_id,
            incoming=incoming,
            node_items=self._output_items,
            label_to_id=label_to_id,
            trigger_data=self._trigger_data,
            variables=self.variables,
            env=self.env,
            secrets=self.secrets,
            loop_data=self.loop_data,
        )
        # Late-bind so inline `{{ $step.x }}` chunks inside literal-text
        # fields route through the same JSONata engine as `=expression`.
        template_resolver._jsonata = jsonata_resolver  # noqa: SLF001
        resolved_properties = resolve_properties(
            node_data.get("data", {}).get("properties", {}),
            jsonata_resolver,
            template_resolver,
        )

        from apps.api.app.core.http import get_http_client

        http_client = await get_http_client()

        # Build run_downstream callback for nodes that handle their own successors (e.g. ForEach).
        # Pre-bind the successor node IDs for this specific node.
        _successor_ids = [
            e["target"]
            for e in self.edges
            if e["source"] == node_id and e.get("sourceHandle") != "error"
        ]

        async def run_downstream(
            item_input: dict[str, Any],
            loop_data: dict[str, Any] | None = None,
        ) -> list[dict[str, Any]]:
            if self._depth + 1 > _MAX_SUBGRAPH_DEPTH:
                raise RuntimeError(
                    f"Execution exceeded the maximum sub-workflow depth ({_MAX_SUBGRAPH_DEPTH})"
                )
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
                    _depth=self._depth + 1,
                    _budget=self._budget,
                )
                sub_runner.variables = self.variables
                sub_runner.env = self.env
                sub_runner.secrets = self.secrets
                sub_runner.loop_data = loop_data or item_input  # expose as {{loop.*}}
                # Crew/loop rounds still resolve {{$trigger.*}} against the
                # original trigger payload, not an empty dict.
                sub_runner._trigger_data = self._trigger_data
                sub_runner._outputs = dict(self._outputs)
                sub_runner._output_items = dict(self._output_items)
                result = await sub_runner._execute_subgraph(start_id, item_input)
                # A failed sub-run yields {} — surface the failure instead
                # of discarding it, so orchestrators (Crew, ForEach) can
                # report WHY a round died rather than silently retrying.
                if sub_runner._failed.is_set() and not result:
                    result = {"status": "failed", "error": sub_runner._error_message}
                results.append(result)
                async with self._lock:
                    self._outputs.update(sub_runner._outputs)
                    self._output_items.update(sub_runner._output_items)
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
            workspace_id=self.workspace_id,
        )

        await self._emit(
            "node_started",
            {
                "node_id": node_id,
                "node_type": node_data.get("type"),
                "label": label,
            },
        )

        # Retry config — read from resolved properties
        max_retries = int(resolved_properties.get("retries") or 0)
        retry_delay_ms = int(resolved_properties.get("retry_delay_ms") or 1000)
        attempt = 0
        result = None
        node_start = time.time()

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

        duration_ms = int((time.time() - node_start) * 1000)

        async with self._lock:
            self._executed[node_id] = result

        for log_msg in result.logs:
            await self._log(log_msg, level="info" if result.success else "error", node_id=node_id)

        next_edges = [e for e in self.edges if e["source"] == node_id]

        if result.success:
            items = self._build_items_with_provenance(result, _source_node_id, _source_item_index)
            async with self._lock:
                self._outputs[node_id] = result.output_data
                self._output_items[node_id] = items

            # Merge explicit + detected artifacts, stamp source, then emit
            # one `artifact.emitted` event per artifact so streaming clients
            # (public app canvas, run-log inspector) can render them as
            # they arrive rather than waiting for the run to finish.
            from apps.api.app.features.apps.artifact_detection import detect_artifacts

            explicit = list(getattr(result, "artifacts", []) or [])
            detected = detect_artifacts(result.output_data or {}, source_node_id=node_id)
            all_artifacts = [
                a.with_source(node_id) if a.metadata.get("source_node_id") is None else a
                for a in explicit
            ] + detected
            if all_artifacts:
                self._collected_artifacts.extend(all_artifacts)
                for art in all_artifacts:
                    await self._emit(
                        "artifact_emitted", {"node_id": node_id, "artifact": art.model_dump()}
                    )

            await self._emit("node_completed", {"node_id": node_id, "output": result.output_data})
            await self._log(
                label,
                node_id=node_id,
                payload={
                    "input": resolved_properties,
                    "data_in": input_data,
                    "output": result.output_data,
                    "duration_ms": duration_ms,
                },
            )

            # If node handled its own successors, don't dispatch edges
            if result.handled_successors:
                return

            branch = result.output_data.get("branch")
            active_edges = [
                e
                for e in next_edges
                if e.get("sourceHandle") != "error"
                and not (branch and e.get("sourceHandle") and e.get("sourceHandle") != branch)
            ]

            if active_edges:
                await asyncio.gather(
                    *[
                        self._execute_node(
                            e["target"],
                            result.output_data,
                            _source_node_id=node_id,
                            _source_item_index=0,
                        )
                        for e in active_edges
                    ]
                )

        else:
            await self._emit("node_failed", {"node_id": node_id, "error": result.error})
            await self._log(
                label,
                level="error",
                node_id=node_id,
                payload={
                    "input": resolved_properties,
                    "data_in": input_data,
                    "error": result.error,
                    "duration_ms": duration_ms,
                },
            )

            error_edges = [e for e in next_edges if e.get("sourceHandle") == "error"]
            if error_edges:
                error_payload = {
                    "input": resolved_properties,
                    "data_in": input_data,
                    "error": result.error,
                }
                await asyncio.gather(
                    *[
                        self._execute_node(
                            e["target"],
                            error_payload,
                            _source_node_id=node_id,
                            _source_item_index=0,
                        )
                        for e in error_edges
                    ]
                )
            else:
                self._failed.set()
                error = result.error or "Unknown error"
                self._error_message = error if "Node" in error else f"Node {label} failed: {error}"
                logger.error(f"Execution failed at node {node_id}: {result.error}")

    async def _resume_from(
        self, paused_node_id: str, resume_input: dict[str, Any]
    ) -> dict[str, Any]:
        """Resume execution after a pause, injecting resume_input as the paused node's output."""
        # Treat paused node as completed with resume_input as its output
        async with self._lock:
            self._executed[paused_node_id] = True
            self._outputs[paused_node_id] = resume_input
            # The paused node didn't go through `_execute_node` post-completion,
            # so build its items list inline from the injected resume payload.
            # No upstream provenance is available here; downstream items will
            # carry `paired_item -> paused_node_id` from the dispatch below.
            self._output_items[paused_node_id] = [NodeItem(data=resume_input)]

        # Follow outgoing edges from the paused node
        next_edges = [e for e in self.edges if e["source"] == paused_node_id]
        if next_edges:
            await asyncio.gather(
                *[
                    self._execute_node(
                        e["target"],
                        resume_input,
                        _source_node_id=paused_node_id,
                        _source_item_index=0,
                    )
                    for e in next_edges
                ]
            )

        if self._failed.is_set():
            raise Exception(self._error_message or "Execution failed")

        if self._outputs:
            return self._outputs[list(self._outputs.keys())[-1]]
        return {}

    async def _execute_subgraph(
        self, start_node_id: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
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

    @staticmethod
    def _build_items_with_provenance(
        result: Any,
        source_node_id: str | None,
        source_item_index: int,
    ) -> list[NodeItem]:
        """Materialise the items list a node emits, stamping default provenance.

        - If the node returned its own ``items`` list, items missing a
          ``paired_item`` get one synthesised from the dispatch provenance.
          Items the node set explicitly are left alone.
        - If the node returned only ``output_data``, a single-item list is
          synthesised with the default provenance attached.
        - When ``source_node_id`` is ``None`` (entry nodes / trigger), items
          keep ``paired_item=None`` — there is no upstream to point to.
        """
        items = result.get_items()
        default_provenance: PairedItem | None = (
            PairedItem(source_node_id=source_node_id, source_item_index=source_item_index)
            if source_node_id is not None
            else None
        )
        if default_provenance is None:
            return items
        for item in items:
            if item.paired_item is None:
                item.paired_item = default_provenance
        return items

    async def _emit(self, event_type: str, data: dict[str, Any]) -> None:
        if self.emitter:
            await self.emitter.emit(event_type, data)

    async def _log(
        self, message: str, level: str = "info", node_id: str | None = None, payload: Any = None
    ) -> None:
        if self.on_log:
            await self.on_log(message, level=level, node_id=node_id, payload=payload)
