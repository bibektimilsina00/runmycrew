from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.models.audit_log import AuditLog


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        action: str,
        resource_type: str,
        resource_id: str,
        resource_name: str,
        meta: dict[str, Any] | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            workspace_id=workspace_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            meta=meta,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def list_for_workspace(
        self,
        workspace_id: uuid.UUID,
        resource_type: str | None = None,
        limit: int = 50,
    ) -> list[AuditLog]:
        q = (
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .where(AuditLog.workspace_id == workspace_id)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )
        if resource_type:
            q = q.where(AuditLog.resource_type == resource_type)
        result = await self.db.execute(q)
        return list(result.scalars().all())
