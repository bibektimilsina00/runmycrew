from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, Index, UniqueConstraint
from sqlmodel import Field

from apps.api.app.shared.sqlmodel import (
    SQLModelBase,
    UTCDateTime,
    created_at_field,
    updated_at_field,
)


class MetaSubscription(SQLModelBase, table=True):
    """One row per (workflow, trigger node) pair that listens to a Meta webhook target.

    Replaces the Phase 1/2 workflow-graph scan with a B-tree-indexed
    lookup on `(object_type, target_id, field)` so webhook fan-out stays
    constant-time as workflow count grows.

    Lifecycle:
      - Upserted by `MetaService.sync_workflow_subscriptions` on every
        workflow save. Stale rows (target removed from graph) are deleted.
      - `meta_subscribed_at` is stamped only after a successful Meta-side
        `subscribed_apps` call. `last_error` is populated on failures so
        the editor can surface a "reconnect required" banner.
      - Cascaded by workspace + user delete; workflow delete is handled
        in `MetaSubscriptionRepository.delete_for_workflow`.
    """

    __table_args__ = (
        UniqueConstraint(
            "workflow_id",
            "node_id",
            name="uq_meta_subscription_workflow_node",
        ),
        Index(
            "ix_meta_subscription_lookup",
            "object_type",
            "target_id",
            "field",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    credential_id: uuid.UUID = Field(foreign_key="credential.id", ondelete="CASCADE", index=True)
    workflow_id: uuid.UUID = Field(foreign_key="workflow.id", ondelete="CASCADE", index=True)
    node_id: str = Field(max_length=128)

    # Routing metadata mirroring what `MetaService._flatten_entry` emits.
    trigger_type: str = Field(max_length=128)
    object_type: str = Field(max_length=64)  # page | instagram | whatsapp_business_account
    target_id: str = Field(max_length=128)  # entry.id Meta sends on the webhook
    field: str = Field(max_length=64)  # synthesized field tag

    # Meta-side subscription state. Tracked separately from row creation
    # so we can retry failed `subscribed_apps` calls without losing the
    # routing knowledge the row already provides.
    is_active: bool = Field(default=True)
    meta_subscribed_at: datetime | None = Field(
        default=None,
        sa_column=Column(UTCDateTime(), nullable=True),
    )
    last_error: str | None = Field(default=None, max_length=1024)

    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()
