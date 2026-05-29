# Execution flow

How a workflow actually runs, end to end. This is the core of the product; the
path is **async via Celery** (there is no synchronous in-API execution).

## The path

```
trigger (manual run / webhook / schedule / a2a)
  → features/*/service.py
  → execution_engine.engine.ExecutionEngine.trigger_workflow()
        • writes an Execution row (status="pending")
        • execute_workflow.delay(...)            ── Celery enqueue (Redis broker)
  → worker: apps/worker/app/jobs/tasks.py::execute_workflow   (Celery task)
        → _run_workflow()
            • loads Workflow, decrypted credentials, and user secrets
            • status → "running"
            • WorkflowRunner.run(trigger_data)
                  └ execution_engine/engine/workflow_runner.py
                  → node_executor → node_system/nodes/<type>
                  → RedisEventEmitter publishes events to Redis
            • status → "completed" | "failed" | "cancelled" | "paused"
```

Realtime: `RedisEventEmitter` publishes `execution_started`, `node_started`,
`node_completed`, `node_failed`, `log_synced`, `execution_completed/failed/
cancelled/paused`. The API relays these to the browser over WebSocket
(`api/v1/websocket`).

## Worker entrypoint

`celery -A apps.worker.app.jobs.tasks worker` (see `Makefile::worker` and
`apps/worker/Dockerfile`). The Celery app is defined in
`apps/api/app/core/celery.py` with `include=["apps.worker.app.jobs.tasks",
"apps.api.app.execution_engine.scheduler.cron"]`. Only one `execute_workflow`
task is registered (name `execute_workflow`).

## Status lifecycle

`pending → running → {completed | failed | cancelled | paused}`. A `paused`
execution (from a Human Input node) stores a snapshot + resume token; resuming
re-enqueues `execute_workflow` with `resume_from`/`snapshot`.

## Control signals

- **Cancel:** a `execution:cancel:<id>` key in Redis; the runner checks it
  before each node and raises `CancelledException`.
- **Retry:** per-node `retries` / `retry_delay_ms` resolved properties.
- **Branching:** edges may carry a `sourceHandle` (`"error"` for error edges, or
  a branch name); the runner routes accordingly.

## Safety / limits

- **CodeNode sandbox (phase A):** `logic.code` runs Python/JS in a **separate
  hardened process** — clean environment (worker secrets/env are *not*
  propagated), OS resource limits (`RLIMIT_CPU`, `RLIMIT_FSIZE`, `RLIMIT_AS` on
  Linux), and a hard timeout that kills the process. This is defense-in-depth,
  **not** full isolation — the child can still reach network/filesystem. True
  isolation (a locked-down container per run) is the planned phase B.
- **Runaway guard:** `WorkflowRunner` shares a node-execution budget
  (`_MAX_NODE_EXECUTIONS = 10_000`) across all sub-runners and caps
  sub-workflow recursion (`_MAX_SUBGRAPH_DEPTH = 50`). Cyclic graphs / runaway
  loops fail fast instead of hanging the worker.

## Tests

- `apps/api/tests/test_execution_path.py` — engine-level (graph runs, failure,
  budget guard, worker import-guard + contract checks). Infra-free.
- `apps/api/tests/test_execution_live.py` — true integration: seeds a workflow +
  execution, runs the real `_run_workflow` against live Postgres + Redis,
  asserts completion. Skips if the DB is unreachable.
- `apps/api/tests/test_code_sandbox.py` — proves the sandbox properties.
