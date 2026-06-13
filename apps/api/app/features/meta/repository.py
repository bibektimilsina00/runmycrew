from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.features.meta.models import MetaSubscription


class MetaSubscriptionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def lookup(
        self,
        object_type: str,
        target_id: str,
        field: str,
    ) -> list[MetaSubscription]:
        """Indexed read used by the webhook receiver. Hits the composite
        `ix_meta_subscription_lookup` index — O(log N) regardless of
        active-workflow count."""
        stmt = select(MetaSubscription).where(
            MetaSubscription.object_type == object_type,
            MetaSubscription.target_id == target_id,
            MetaSubscription.field == field,
            MetaSubscription.is_active.is_(True),
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def list_for_workflow(self, workflow_id: uuid.UUID) -> list[MetaSubscription]:
        stmt = select(MetaSubscription).where(MetaSubscription.workflow_id == workflow_id)
        return list((await self.db.execute(stmt)).scalars().all())

    async def list_for_target(
        self,
        credential_id: uuid.UUID,
        object_type: str,
        target_id: str,
    ) -> list[MetaSubscription]:
        """Used to decide whether unsubscribing a target on Meta's side would
        orphan another active workflow on the same credential."""
        stmt = select(MetaSubscription).where(
            MetaSubscription.credential_id == credential_id,
            MetaSubscription.object_type == object_type,
            MetaSubscription.target_id == target_id,
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def upsert(self, sub: MetaSubscription) -> MetaSubscription:
        """Insert-or-update keyed on `(workflow_id, node_id)`. Returns the
        live row so callers can read auto-stamped timestamps."""
        existing = await self._get_for_node(sub.workflow_id, sub.node_id)
        if existing is None:
            self.db.add(sub)
            await self.db.flush()
            return sub
        # Update mutable fields in-place. Identity (credential, target,
        # field) shouldn't drift for the same (workflow, node) — if the
        # user edited the trigger to point at a new target id we replace
        # the row contents wholesale.
        existing.credential_id = sub.credential_id
        existing.trigger_type = sub.trigger_type
        existing.object_type = sub.object_type
        existing.target_id = sub.target_id
        existing.field = sub.field
        existing.is_active = sub.is_active
        # Meta-side subscribe timestamps + error reset when target changes;
        # the resync loop will re-call subscribed_apps and re-stamp.
        if existing.target_id != sub.target_id or existing.object_type != sub.object_type:
            existing.meta_subscribed_at = None
            existing.last_error = None
        await self.db.flush()
        return existing

    async def delete_for_workflow(self, workflow_id: uuid.UUID) -> list[MetaSubscription]:
        """Returns the rows that were deleted so the caller can decide
        whether to unsubscribe their targets on Meta's side."""
        rows = await self.list_for_workflow(workflow_id)
        if not rows:
            return []
        await self.db.execute(
            delete(MetaSubscription).where(MetaSubscription.workflow_id == workflow_id)
        )
        return rows

    async def delete_missing_nodes(
        self,
        workflow_id: uuid.UUID,
        keep_node_ids: set[str],
    ) -> list[MetaSubscription]:
        """Drop rows for nodes the workflow no longer carries.

        Used during graph sync: enumerate the workflow's current Meta
        trigger node ids, then remove any subscription rows pointing at
        ids that are no longer in the graph (the node was deleted or its
        type changed).
        """
        rows = await self.list_for_workflow(workflow_id)
        to_drop = [r for r in rows if r.node_id not in keep_node_ids]
        if not to_drop:
            return []
        ids = [r.id for r in to_drop]
        await self.db.execute(delete(MetaSubscription).where(MetaSubscription.id.in_(ids)))
        return to_drop

    async def _get_for_node(
        self,
        workflow_id: uuid.UUID,
        node_id: str,
    ) -> MetaSubscription | None:
        stmt = select(MetaSubscription).where(
            MetaSubscription.workflow_id == workflow_id,
            MetaSubscription.node_id == node_id,
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()
