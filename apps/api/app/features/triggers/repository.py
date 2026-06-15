from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.features.triggers.models import IntegrationTriggerState, TriggerFixture


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


class IntegrationTriggerStateRepository:
    """CRUD for the per-(workflow, node) cursor that drives polling triggers.

    Polling-based triggers (Gmail / Calendar / Drive / Sheets / …) live
    or die by this cursor — without it every poll either re-emits old
    items or never advances. Centralising the persistence here keeps
    each trigger node small (it owns the cursor *shape*, not the I/O).
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(
        self,
        workflow_id: uuid.UUID,
        node_id: str,
    ) -> IntegrationTriggerState | None:
        stmt = select(IntegrationTriggerState).where(
            IntegrationTriggerState.workflow_id == workflow_id,
            IntegrationTriggerState.node_id == node_id,
        )
        return (await self.db.execute(stmt)).scalars().first()

    async def upsert(
        self,
        *,
        workflow_id: uuid.UUID,
        workspace_id: uuid.UUID,
        node_id: str,
        provider: str,
        cursor: dict[str, Any],
        last_polled_at: datetime | None = None,
        next_poll_at: datetime | None = None,
        last_error: str | None = None,
    ) -> IntegrationTriggerState:
        """Insert or update the cursor row for a polling trigger.

        Callers pass the *new* cursor + the *new* schedule; the row's
        timestamps fall back to `now()` for `last_polled_at` so the
        editor's "last fired" UI stays truthful even when the trigger
        node forgets to set it explicitly.
        """
        now = datetime.now(UTC)
        existing = await self.get(workflow_id, node_id)
        if existing is None:
            row = IntegrationTriggerState(
                workflow_id=workflow_id,
                workspace_id=workspace_id,
                node_id=node_id,
                provider=provider,
                cursor=cursor,
                last_polled_at=last_polled_at or now,
                next_poll_at=next_poll_at,
                last_error=last_error,
            )
            self.db.add(row)
            await self.db.flush()
            return row
        existing.provider = provider
        existing.cursor = cursor
        existing.last_polled_at = last_polled_at or now
        existing.next_poll_at = next_poll_at
        existing.last_error = last_error
        await self.db.flush()
        return existing

    async def list_due(
        self,
        *,
        provider: str | None = None,
        limit: int = 50,
    ) -> list[IntegrationTriggerState]:
        """Return rows whose `next_poll_at <= now()`, ordered by oldest
        first. The polling scheduler reads this to decide which triggers
        to fan out on the current tick.
        """
        now = datetime.now(UTC)
        stmt = select(IntegrationTriggerState).where(
            IntegrationTriggerState.next_poll_at.is_not(None),
            IntegrationTriggerState.next_poll_at <= now,
        )
        if provider is not None:
            stmt = stmt.where(IntegrationTriggerState.provider == provider)
        stmt = stmt.order_by(IntegrationTriggerState.next_poll_at).limit(limit)
        return list((await self.db.execute(stmt)).scalars().all())

    async def delete(self, workflow_id: uuid.UUID, node_id: str) -> None:
        row = await self.get(workflow_id, node_id)
        if row is None:
            return
        await self.db.delete(row)
        await self.db.flush()
