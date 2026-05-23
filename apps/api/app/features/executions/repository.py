from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.core.database import get_db
from apps.api.app.features.workflows.models import Execution, ExecutionLog, Workflow


class ExecutionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def publish_run_update(self, execution_id: uuid.UUID) -> None:
        try:
            import json

            from apps.api.app.core.redis import get_redis

            result = await self.db.execute(
                select(
                    Execution.id,
                    Execution.workflow_id,
                    Execution.status,
                    Execution.trigger_type,
                    Execution.started_at,
                    Execution.finished_at,
                    Workflow.name.label("workflow_name"),
                    Workflow.color.label("workflow_color"),
                    Workflow.workspace_id.label("workspace_id"),
                )
                .join(Workflow, Execution.workflow_id == Workflow.id)
                .where(Execution.id == execution_id)
            )
            row = result.fetchone()
            if not row:
                return

            r = row._mapping
            run_data = {
                "id": str(r["id"]),
                "workflow_id": str(r["workflow_id"]),
                "workflow_name": r["workflow_name"],
                "workflow_color": r["workflow_color"],
                "status": r["status"],
                "trigger_type": r["trigger_type"],
                "started_at": r["started_at"].isoformat() if r["started_at"] else None,
                "finished_at": r["finished_at"].isoformat() if r["finished_at"] else None,
                "duration_ms": (
                    int((r["finished_at"] - r["started_at"]).total_seconds() * 1000)
                    if r["started_at"] and r["finished_at"]
                    else None
                ),
            }

            redis = await get_redis()
            event = {
                "type": "run_updated",
                "run": run_data,
            }
            channel = f"workspace:{r['workspace_id']}:runs"
            await redis.publish(channel, json.dumps(event))
        except Exception as e:
            from apps.api.app.core.logger import get_logger

            get_logger(__name__).warning(f"Failed to publish run update for {execution_id}: {e}")

    async def create(self, execution: Execution) -> Execution:
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)
        await self.publish_run_update(execution.id)
        return execution

    async def get_by_id(self, execution_id: uuid.UUID) -> Execution | None:
        result = await self.db.execute(
            select(Execution)
            .where(Execution.id == execution_id)
            .options(selectinload(Execution.logs))
        )
        return result.scalar_one_or_none()

    async def list_by_workflow(self, workflow_id: uuid.UUID) -> list[Execution]:
        result = await self.db.execute(
            select(Execution)
            .where(Execution.workflow_id == workflow_id)
            .order_by(Execution.started_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        execution_id: uuid.UUID,
        status: str,
        output_data: dict | None = None,
    ) -> None:
        result = await self.db.execute(select(Execution).where(Execution.id == execution_id))
        execution = result.scalar_one_or_none()
        if execution:
            execution.status = status
            if status == "running":
                execution.started_at = datetime.now(UTC)
            elif status in ("completed", "failed", "cancelled"):
                execution.finished_at = datetime.now(UTC)
            if output_data is not None:
                execution.output_data = output_data
            await self.db.commit()
            await self.publish_run_update(execution_id)

    async def add_log(
        self,
        execution_id: uuid.UUID,
        message: str,
        level: str = "info",
        node_id: str | None = None,
        payload: dict | None = None,
    ) -> None:
        log = ExecutionLog(
            execution_id=execution_id,
            node_id=node_id,
            level=level,
            message=message,
            payload=payload,
        )
        self.db.add(log)
        await self.db.commit()

    async def save_pause(
        self,
        execution_id: uuid.UUID,
        node_id: str,
        resume_token: str,
        resume_schema: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> None:
        result = await self.db.execute(select(Execution).where(Execution.id == execution_id))
        execution = result.scalar_one_or_none()
        if execution:
            execution.status = "paused"
            execution.paused_node_id = node_id
            execution.resume_token = resume_token
            execution.resume_schema = resume_schema
            execution.snapshot = snapshot
            await self.db.commit()
            await self.publish_run_update(execution_id)

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        workflow_id: uuid.UUID | None = None,
    ) -> tuple[list[dict], int]:
        """Return executions for all workflows owned by user, with workflow name."""
        q = (
            select(
                Execution.id,
                Execution.workflow_id,
                Execution.status,
                Execution.trigger_type,
                Execution.started_at,
                Execution.finished_at,
                Workflow.name.label("workflow_name"),
                Workflow.color.label("workflow_color"),
            )
            .join(Workflow, Execution.workflow_id == Workflow.id)
            .where(Workflow.user_id == user_id)
        )
        if status:
            q = q.where(Execution.status == status)
        if workflow_id:
            q = q.where(Execution.workflow_id == workflow_id)

        total_result = await self.db.execute(select(func.count()).select_from(q.subquery()))
        total = total_result.scalar() or 0

        q = q.order_by(Execution.started_at.desc()).limit(limit).offset(offset)
        rows = await self.db.execute(q)
        return [dict(r._mapping) for r in rows.fetchall()], total

    async def list_by_workspace(
        self,
        workspace_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        workflow_id: uuid.UUID | None = None,
    ) -> tuple[list[dict], int]:
        q = (
            select(
                Execution.id,
                Execution.workflow_id,
                Execution.status,
                Execution.trigger_type,
                Execution.started_at,
                Execution.finished_at,
                Workflow.name.label("workflow_name"),
                Workflow.color.label("workflow_color"),
            )
            .join(Workflow, Execution.workflow_id == Workflow.id)
            .where(Workflow.workspace_id == workspace_id)
        )
        if status:
            q = q.where(Execution.status == status)
        if workflow_id:
            q = q.where(Execution.workflow_id == workflow_id)

        total_result = await self.db.execute(select(func.count()).select_from(q.subquery()))
        total = total_result.scalar() or 0

        q = q.order_by(Execution.started_at.desc()).limit(limit).offset(offset)
        rows = await self.db.execute(q)
        return [dict(r._mapping) for r in rows.fetchall()], total

    async def last_run_by_workflow(self, workflow_ids: list[uuid.UUID]) -> dict[str, dict]:
        """Return most recent execution info keyed by workflow_id string."""
        if not workflow_ids:
            return {}
        # Subquery: max started_at per workflow
        sub = (
            select(Execution.workflow_id, func.max(Execution.started_at).label("max_started"))
            .where(Execution.workflow_id.in_(workflow_ids))
            .group_by(Execution.workflow_id)
            .subquery()
        )
        result = await self.db.execute(
            select(Execution.workflow_id, Execution.started_at, Execution.status).join(
                sub,
                (Execution.workflow_id == sub.c.workflow_id)
                & (Execution.started_at == sub.c.max_started),
            )
        )
        return {
            str(row.workflow_id): {"started_at": row.started_at, "status": row.status}
            for row in result.fetchall()
        }

    async def count_by_workflow(self, workflow_ids: list[uuid.UUID]) -> dict[str, int]:
        """Return execution counts keyed by workflow_id string."""
        if not workflow_ids:
            return {}
        result = await self.db.execute(
            select(Execution.workflow_id, func.count(Execution.id))
            .where(Execution.workflow_id.in_(workflow_ids))
            .group_by(Execution.workflow_id)
        )
        return {str(row[0]): row[1] for row in result.fetchall()}

    async def get_paused(self, execution_id: uuid.UUID, resume_token: str) -> Execution | None:
        result = await self.db.execute(
            select(Execution).where(
                Execution.id == execution_id,
                Execution.status == "paused",
                Execution.resume_token == resume_token,
            )
        )
        return result.scalar_one_or_none()

    async def get_logs_by_workspace(
        self,
        workspace_id: uuid.UUID,
        limit: int = 100,
        level: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve execution logs across all workflows in a workspace."""
        q = (
            select(
                ExecutionLog.id,
                ExecutionLog.timestamp,
                ExecutionLog.level,
                ExecutionLog.message,
                Workflow.name.label("workflow_name"),
            )
            .join(Execution, ExecutionLog.execution_id == Execution.id)
            .join(Workflow, Execution.workflow_id == Workflow.id)
            .where(Workflow.workspace_id == workspace_id)
        )
        if level:
            q = q.where(ExecutionLog.level == level)

        q = q.order_by(ExecutionLog.timestamp.desc()).limit(limit)

        result = await self.db.execute(q)
        rows = result.fetchall()

        return [
            {
                "id": str(r.id),
                "t": r.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if r.timestamp else "",
                "lvl": "err" if r.level == "error" else ("warn" if r.level == "warn" else "info"),
                "src": r.workflow_name,
                "msg": r.message,
            }
            for r in rows
        ]


def get_execution_repository(db: AsyncSession = Depends(get_db)) -> ExecutionRepository:
    return ExecutionRepository(db)
