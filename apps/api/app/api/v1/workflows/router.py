import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.core.database import get_db
from apps.api.app.models.user import User
from apps.api.app.schemas.workflow import (
    WorkflowBatchUpdate,
    WorkflowCreate,
    WorkflowOut,
    WorkflowUpdate,
)
from apps.api.app.services.workflow_service import WorkflowService

router = APIRouter()


@router.get("/with-stats")
async def list_workflows_with_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowService(db)
    workflows = await service.list_workflows(current_user)
    from apps.api.app.repositories.execution_repository import ExecutionRepository
    repo = ExecutionRepository(db)
    counts = await repo.count_by_workflow([w.id for w in workflows])
    return [
        {
            **w.model_dump(),
            "id": str(w.id),
            "user_id": str(w.user_id),
            "folder_id": str(w.folder_id) if w.folder_id else None,
            "created_at": w.created_at.isoformat(),
            "updated_at": w.updated_at.isoformat(),
            "execution_count": counts.get(str(w.id), 0),
        }
        for w in workflows
    ]


@router.get("/", response_model=list[WorkflowOut])
async def list_workflows(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowService(db)
    return await service.list_workflows(current_user)


@router.post("/", response_model=WorkflowOut, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    data: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowService(db)
    return await service.create_workflow(data, current_user)


@router.get("/{workflow_id}", response_model=WorkflowOut)
async def get_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowService(db)
    return await service.get_workflow(workflow_id, current_user)


@router.put("/{workflow_id}", response_model=WorkflowOut)
async def update_workflow(
    workflow_id: uuid.UUID,
    data: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id, current_user)

    # Auto-snapshot before saving if graph is changing
    if data.graph is not None and data.graph != workflow.graph:
        await _create_version(db, workflow_id, workflow.graph)

    return await service.update_workflow(workflow_id, data, current_user)


async def _create_version(db, workflow_id: uuid.UUID, graph: dict) -> None:
    import json as _json
    import sqlalchemy as sa
    from apps.api.app.models.workflow_version import WorkflowVersion

    result = await db.execute(
        sa.select(sa.func.count()).select_from(WorkflowVersion).where(WorkflowVersion.workflow_id == workflow_id)
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
    db: AsyncSession = Depends(get_db),
):
    import sqlalchemy as sa
    from apps.api.app.models.workflow_version import WorkflowVersion

    service = WorkflowService(db)
    await service.get_workflow(workflow_id, current_user)  # ownership check

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
    db: AsyncSession = Depends(get_db),
):
    import json as _json
    import sqlalchemy as sa
    from apps.api.app.models.workflow_version import WorkflowVersion

    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id, current_user)

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
    return await service.update_workflow(workflow_id, WorkflowUpdate(graph=graph), current_user)


@router.patch("/batch", status_code=status.HTTP_204_NO_CONTENT)
async def batch_update_workflows(
    data: WorkflowBatchUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from apps.api.app.core.logger import logger

    logger.info(f"Received batch update request: {data.model_dump_json()}")
    service = WorkflowService(db)
    await service.batch_update_workflows(data, current_user)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowService(db)
    await service.delete_workflow(workflow_id, current_user)


@router.post("/{workflow_id}/duplicate", response_model=WorkflowOut)
async def duplicate_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowService(db)
    source = await service.get_workflow(workflow_id, current_user)

    from apps.api.app.schemas.workflow import WorkflowCreate
    import copy

    data = WorkflowCreate(
        name=f"{source.name} (copy)",
        description=source.description,
        folder_id=source.folder_id,
        graph=copy.deepcopy(source.graph),
        color=source.color,
    )
    return await service.create_workflow(data, current_user)


@router.post("/{workflow_id}/run")
async def run_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    graph: dict[str, Any] | None = Body(default=None),
):
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id, current_user)

    from apps.api.app.execution_engine.engine import execution_engine

    execution_id = await execution_engine.trigger_workflow(
        workflow_id=workflow.id,
        # Use client-provided graph if present (avoids auto-save race condition),
        # fall back to persisted graph otherwise.
        graph=graph if graph is not None else workflow.graph,
        trigger_type="manual",
    )
    return {"execution_id": str(execution_id)}
