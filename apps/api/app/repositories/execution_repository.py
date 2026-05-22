from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.models import Execution, ExecutionLog
from apps.api.app.models.workflow import Workflow


class ExecutionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, execution: Execution) -> Execution:
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)
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

