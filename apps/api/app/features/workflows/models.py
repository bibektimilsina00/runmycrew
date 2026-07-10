import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship

from apps.api.app.shared.sqlmodel import SQLModelBase, created_at_field, updated_at_field

if TYPE_CHECKING:
    from apps.api.app.features.executions.models import Execution
    from apps.api.app.features.folders.models import Folder
    from apps.api.app.features.users.models import User


class Workflow(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    description: str | None = Field(default=None)
    schema_version: str = Field(default="1.0.0")
    graph: dict[str, Any] = Field(
        default_factory=lambda: {"nodes": [], "edges": []},
        sa_column=Column(JSON, nullable=False, default=lambda: {"nodes": [], "edges": []}),
    )
    is_active: bool = Field(default=False)
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()
    position: int = Field(default=0)
    color: str | None = Field(default=None, max_length=50)
    env: dict[str, str] | None = Field(default=None, sa_column=Column(JSON))
    version_vector: int = Field(default=0)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    folder_id: uuid.UUID | None = Field(
        default=None, foreign_key="folder.id", ondelete="CASCADE", index=True
    )

    # ── Loop engineering — phases 2 + 5 ───────────────────────────
    # See docs/loop-engineering-plan.md sections 8.5 + 8.6.
    #
    # concurrency_policy controls what happens when a trigger fires
    # this workflow while a previous run is still in flight:
    #   - "skip"    — drop the new fire (default; safest for loops)
    #   - "queue"   — wait up to concurrency_queue_max_wait_seconds
    #   - "replace" — force-acquire, original holder stays running
    #                 but its release becomes a no-op
    concurrency_policy: str = Field(default="skip", max_length=16)
    concurrency_queue_max_wait_seconds: int = Field(default=60)

    # cron_drift_policy controls what happens when the cron scheduler
    # is late firing (e.g. the worker was busy + slept past the tick).
    #   - "latest"  — fire ONCE for the current tick only (default)
    #   - "catchup" — fire for every missed tick since last run
    #   - "skip"    — fire nothing if we are more than 1 tick late
    cron_drift_policy: str = Field(default="latest", max_length=16)

    # ── Loop engineering — workflow kind discriminator ────────────
    # "automation" = the full n8n-style editor (all nodes).
    # "loop"       = the focused loop-engineering editor (AI-orchestration
    #                nodes only). See docs/loop-engineering-plan.md.
    kind: str = Field(default="automation", max_length=16)

    # Hashed secrets for the ``trigger.chat_app`` visitor auth flow. Kept
    # here instead of in the graph JSON so they never leak in a workflow
    # export. Nullable — populated only when the owner sets a password /
    # generates an API key from the Share dialog.
    app_password_hash: str | None = Field(default=None)
    app_api_key_hash: str | None = Field(default=None)

    user: "User" = Relationship(back_populates="workflows")
    folder: "Folder" = Relationship(back_populates="workflows")
    executions: list["Execution"] = Relationship(
        back_populates="workflow", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class WorkflowVersion(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workflow_id: uuid.UUID = Field(foreign_key="workflow.id", ondelete="CASCADE", index=True)
    version: int = Field()
    label: str | None = Field(default=None, max_length=200)
    graph: str = Field()
    created_at: datetime = created_at_field()
