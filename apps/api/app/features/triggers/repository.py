from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.features.triggers.models import TriggerFixture


class TriggerFixtureRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(
        self,
        workflow_id: uuid.UUID,
        node_id: str,
    ) -> TriggerFixture | None:
        stmt = select(TriggerFixture).where(
            TriggerFixture.workflow_id == workflow_id,
            TriggerFixture.node_id == node_id,
        )
        return (await self.db.execute(stmt)).scalars().first()

    async def upsert(
        self,
        *,
        workflow_id: uuid.UUID,
        workspace_id: uuid.UUID,
        node_id: str,
        payload: dict[str, Any],
        source: str = "webhook",
    ) -> TriggerFixture:
        """Insert or overwrite the fixture for `(workflow_id, node_id)`.

        Always stamps `captured_at` to now — fixtures are an
        append-overwrite log, not a journal. The DB unique constraint
        on `(workflow_id, node_id)` keeps the row count bounded.
        """
        existing = await self.get(workflow_id, node_id)
        now = datetime.now(UTC)
        if existing is None:
            row = TriggerFixture(
                workflow_id=workflow_id,
                workspace_id=workspace_id,
                node_id=node_id,
                payload=payload,
                source=source,
                captured_at=now,
            )
            self.db.add(row)
            await self.db.flush()
            return row
        existing.payload = payload
        existing.source = source
        existing.captured_at = now
        await self.db.flush()
        return existing
