import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.features.users.models import User
from apps.api.app.features.workflows.schemas import (
    WorkflowBatchUpdate,
    WorkflowCreate,
    WorkflowOut,
    WorkflowUpdate,
)
from apps.api.app.features.workflows.service import WorkflowService
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.features.workspaces.service import WorkspaceService
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

router = APIRouter()

# Node type prefixes that indicate an agentic workflow
_AGENT_NODE_TYPES = {
    "action.agent",
    "action.llm",
    "action.a2a",
    "action.evaluator",
    "action.thinking",
    "action.browser_use",
    "action.vision",
}
_CRON_NODE_TYPES = {"trigger.cron"}


def _derive_kind(graph: dict) -> str:
    """Compute flow / agent / schedule from node types in the graph."""
    nodes = graph.get("nodes", []) if graph else []
    types = {n.get("type", "") for n in nodes}
    if types & _CRON_NODE_TYPES:
        return "schedule"
    if types & _AGENT_NODE_TYPES:
        return "agent"
    return "flow"


def _derive_trigger(graph: dict) -> str:
    """Return the trigger node type string, or 'manual'."""
    nodes = graph.get("nodes", []) if graph else []
    for n in nodes:
        t = n.get("type", "")
        if t.startswith("trigger."):
            return t
    return "manual"


def _derive_cron_info(graph: dict) -> dict | None:
    """Extract cron_expression + timezone from a trigger.cron node."""
    nodes = graph.get("nodes", []) if graph else []
    for n in nodes:
        if n.get("type") == "trigger.cron":
            props = (n.get("data") or {}).get("properties") or {}
            return {
                "cron_expression": props.get("cron_expression", ""),
                "timezone": props.get("timezone", "UTC"),
            }
    return None


def _compute_next_run(cron_expr: str, timezone: str = "UTC") -> str | None:
    """Return ISO string of the next scheduled run, or None on error."""
    try:
        import datetime as _dt
        from zoneinfo import ZoneInfo

        from croniter import croniter

        tz = ZoneInfo(timezone)
        now = _dt.datetime.now(tz)
        ci = croniter(cron_expr, now)
        nxt = ci.get_next(_dt.datetime)
        return nxt.isoformat()
    except Exception:
        return None


def _derive_status(workflow, last_run: dict | None) -> str:
    """Derive human status from is_active + last execution result."""
    if not workflow.is_active:
        # Never run → draft; has runs → paused
        return "paused" if last_run else "draft"
    if last_run and last_run.get("status") == "failed":
        return "error"
    return "active"


def _fmt_last_run(last_run: dict | None) -> str | None:
    if not last_run or not last_run.get("started_at"):
        return None
    from datetime import UTC
    from datetime import datetime as dt

    ts = last_run["started_at"]
    if isinstance(ts, str):
        ts = dt.fromisoformat(ts)
    diff = dt.now(UTC) - ts.replace(tzinfo=UTC) if ts.tzinfo is None else dt.now(UTC) - ts
    secs = int(diff.total_seconds())
    if secs < 60:
        return "just now"
    if secs < 3600:
        return f"{secs // 60}m ago"
    if secs < 86400:
        return f"{secs // 3600}h ago"
    return f"{secs // 86400}d ago"


@router.get("/with-stats")
async def list_workflows_with_stats(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    from apps.api.app.features.executions.repository import ExecutionRepository

    service = WorkflowService(db)
    repo = ExecutionRepository(db)
    workflows = await service.list_workflows(current_user, workspace)
    wf_ids = [w.id for w in workflows]
    counts = await repo.count_by_workflow(wf_ids)
    last_runs = await repo.last_run_by_workflow(wf_ids)

    result = []
    for w in workflows:
        wid = str(w.id)
        last_run = last_runs.get(wid)
        kind = _derive_kind(w.graph)
        cron_info = _derive_cron_info(w.graph) if kind == "schedule" else None
        next_run = (
            _compute_next_run(cron_info["cron_expression"], cron_info["timezone"])
            if cron_info
            else None
        )
        result.append(
            {
                "id": wid,
                "name": w.name,
                "description": w.description,
                "is_active": w.is_active,
                "color": w.color,
                "folder_id": str(w.folder_id) if w.folder_id else None,
                "workspace_id": str(w.workspace_id),
                "user_id": str(w.user_id),
                "created_at": w.created_at.isoformat(),
                "updated_at": w.updated_at.isoformat(),
                # computed
                "kind": kind,
                "trigger": _derive_trigger(w.graph),
                "status": _derive_status(w, last_run),
                "execution_count": counts.get(wid, 0),
                "last_run": _fmt_last_run(last_run),
                "last_run_status": last_run.get("status") if last_run else None,
                # schedule-only
                "cron_expression": cron_info["cron_expression"] if cron_info else None,
                "timezone": cron_info["timezone"] if cron_info else None,
                "next_run": next_run,
            }
        )
    return result


@router.get("/", response_model=list[WorkflowOut])
async def list_workflows(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowService(db)
    return await service.list_workflows(current_user, workspace)


@router.post("/", response_model=WorkflowOut, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    data: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    service = WorkflowService(db)
    return await service.create_workflow(data, current_user, workspace)


@router.get("/{workflow_id}", response_model=WorkflowOut)
async def get_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowService(db)
    return await service.get_workflow(workflow_id, current_user, workspace)


@router.put("/{workflow_id}", response_model=WorkflowOut)
async def update_workflow(
    workflow_id: uuid.UUID,
    data: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id, current_user, workspace)

    # Auto-snapshot before saving if graph is changing
    if data.graph is not None and data.graph != workflow.graph:
        await _create_version(db, workflow_id, workflow.graph)

    return await service.update_workflow(workflow_id, data, current_user, workspace)


async def _create_version(db, workflow_id: uuid.UUID, graph: dict) -> None:
    import json as _json

    import sqlalchemy as sa

    from apps.api.app.features.workflows.models import WorkflowVersion

    result = await db.execute(
        sa.select(sa.func.count())
        .select_from(WorkflowVersion)
        .where(WorkflowVersion.workflow_id == workflow_id)
    )
    count = result.scalar() or 0
    version = WorkflowVersion(
        workflow_id=workflow_id,
        version=count + 1,
        graph=_json.dumps(graph),
    )
    db.add(version)
    await db.commit()


@router.get("/{workflow_id}/versions")
async def list_versions(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    import sqlalchemy as sa

    from apps.api.app.features.workflows.models import WorkflowVersion

    service = WorkflowService(db)
    await service.get_workflow(workflow_id, current_user, workspace)

    result = await db.execute(
        sa.select(WorkflowVersion)
        .where(WorkflowVersion.workflow_id == workflow_id)
        .order_by(WorkflowVersion.version.desc())
        .limit(20)
    )
    versions = result.scalars().all()
    return [
        {
            "id": str(v.id),
            "version": v.version,
            "label": v.label,
            "created_at": v.created_at.isoformat(),
        }
        for v in versions
    ]


@router.post("/{workflow_id}/versions/{version_id}/restore", response_model=WorkflowOut)
async def restore_version(
    workflow_id: uuid.UUID,
    version_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    import json as _json

    import sqlalchemy as sa

    from apps.api.app.features.workflows.models import WorkflowVersion

    service = WorkflowService(db)
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    workflow = await service.get_workflow(workflow_id, current_user, workspace)

    result = await db.execute(
        sa.select(WorkflowVersion).where(
            WorkflowVersion.id == version_id,
            WorkflowVersion.workflow_id == workflow_id,
        )
    )
    v = result.scalar_one_or_none()
    if not v:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Version not found")

    # Snapshot current before restoring
    await _create_version(db, workflow_id, workflow.graph)

    graph = _json.loads(v.graph)
    return await service.update_workflow(
        workflow_id, WorkflowUpdate(graph=graph), current_user, workspace
    )


@router.patch("/batch", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def batch_update_workflows(
    data: WorkflowBatchUpdate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    from apps.api.app.core.logger import logger

    logger.info(f"Received batch update request: {data.model_dump_json()}")
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    service = WorkflowService(db)
    await service.batch_update_workflows(data, current_user, workspace)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    service = WorkflowService(db)
    await service.delete_workflow(workflow_id, current_user, workspace)


@router.patch("/{workflow_id}/toggle")
async def toggle_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Toggle is_active (pause ↔ resume)."""
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id, current_user, workspace)
    updated = await service.update_workflow(
        workflow_id, WorkflowUpdate(is_active=not workflow.is_active), current_user, workspace
    )
    return {"id": str(updated.id), "is_active": updated.is_active}


@router.post("/{workflow_id}/duplicate", response_model=WorkflowOut)
async def duplicate_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowService(db)
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    source = await service.get_workflow(workflow_id, current_user, workspace)

    import copy

    from apps.api.app.features.workflows.schemas import WorkflowCreate

    data = WorkflowCreate(
        name=f"{source.name} (copy)",
        description=source.description,
        folder_id=source.folder_id,
        graph=copy.deepcopy(source.graph),
        color=source.color,
    )
    return await service.create_workflow(data, current_user, workspace)


@router.post("/{workflow_id}/run")
async def run_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    graph: dict[str, Any] | None = Body(default=None),
):
    service = WorkflowService(db)
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    workflow = await service.get_workflow(workflow_id, current_user, workspace)

    from apps.api.app.execution_engine.engine import execution_engine

    execution_id = await execution_engine.trigger_workflow(
        workflow_id=workflow.id,
        # Use client-provided graph if present (avoids auto-save race condition),
        # fall back to persisted graph otherwise.
        graph=graph if graph is not None else workflow.graph,
        trigger_type="manual",
    )
    return {"execution_id": str(execution_id)}
