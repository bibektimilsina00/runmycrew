from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class NodeContext:
    execution_id: str
    workflow_id: str
    node_id: str
    variables: dict[str, Any]
    credentials: list[dict[str, Any]]
    http_client: httpx.AsyncClient
    db: AsyncSession | None = None
    emitter: Any = None  # IEventEmitter — injected by WorkflowRunner
    # Injected by WorkflowRunner: run this node's successor sub-graphs with given input.
    # Pre-bound to the current node's outgoing edge targets.
    # Returns list of output dicts (one per successor branch).
    run_downstream: Any = None  # async callable: (input_data: dict) -> list[dict]
    # Injected by WorkflowRunner: pause this execution (raises PauseSignal)
    pause: Any = None  # async callable: (resume_schema: dict) -> never
    # The workspace the workflow lives in. Polling triggers persist their
    # per-(workflow, node) cursor row keyed on this so deletes cascade
    # cleanly; the runner reads it off the workflow record at boot. When
    # the context can't determine a workspace (synthetic test runs), this
    # stays None and the trigger falls back to stateless preview mode.
    workspace_id: str | None = None
