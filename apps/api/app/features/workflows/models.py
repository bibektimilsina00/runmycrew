from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Column, DateTime
from sqlalchemy.types import TypeDecorator
from sqlmodel import Field, Relationship
from sqlalchemy.orm import relationship

from apps.api.app.shared.sqlmodel import SQLModelBase, utc_now

if TYPE_CHECKING:
    from apps.api.app.features.folders.models import Folder
    from apps.api.app.features.users.models import User


class UTCDateTime(TypeDecorator):
    """Execution timestamp type that always returns timezone-aware UTC datetimes."""

    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(DateTime(timezone=True))

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


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
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now, sa_column_kwargs={"onupdate": utc_now})
    position: int = Field(default=0)
    color: str | None = Field(default=None, max_length=50)
    env: dict[str, str] | None = Field(default=None, sa_column=Column(JSON))
    version_vector: int = Field(default=0)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    folder_id: uuid.UUID | None = Field(
        default=None, foreign_key="folder.id", ondelete="CASCADE", index=True
    )

    user: User = Relationship(from apps.api.app.features.folders.models import Folder
    from apps.api.app.features.users.models import User


class UTCDateTime(TypeDecorator):
    """Execution timestamp type that always returns timezone-aware UTC datetimes."""

    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(DateTime(timezone=True))

    def process_bind_param(self, value: datetime = Relationship(sa_relationship=relationship("datetime", back_populates="workflows")
    folder: Folder | None = Relationship(sa_relationship=relationship("Folder", back_populates="workflows")
    executions: list["Execution"] = Relationship(sa_relationship=relationship("Execution", 
        back_populates="workflow", cascade="all, delete-orphan")


class WorkflowVersion(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workflow_id: uuid.UUID = Field(foreign_key="workflow.id", ondelete="CASCADE", index=True)
    version: int = Field()
    label: str | None = Field(default=None, max_length=200)
    graph: str = Field()
    created_at: datetime = Field(default_factory=utc_now)


class Execution(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workflow_id: uuid.UUID = Field(foreign_key="workflow.id", ondelete="CASCADE", index=True)
    status: str = Field(default="pending")
    trigger_type: str = Field()
    input_data: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    output_data: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    started_at: datetime | None = Field(default=None, sa_column=Column(UTCDateTime()))
    finished_at: datetime | None = Field(default=None, sa_column=Column(UTCDateTime()))
    snapshot: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    resume_token: str | None = Field(default=None)
    resume_schema: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    paused_node_id: str | None = Field(default=None)

    workflow: Workflow = Relationship(id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workflow_id: uuid.UUID = Field(foreign_key="workflow.id", ondelete="CASCADE", index=True)
    version: int = Field()
    label: str = Relationship(sa_relationship=relationship("str", back_populates="executions")
    logs: list["ExecutionLog"] = Relationship(sa_relationship=relationship("ExecutionLog", 
        back_populates="execution", cascade="all, delete-orphan")


class ExecutionLog(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    execution_id: uuid.UUID = Field(foreign_key="execution.id", ondelete="CASCADE", index=True)
    node_id: str | None = Field(default=None)
    level: str = Field(default="info")
    message: str = Field()
    payload: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    timestamp: datetime = Field(
        default_factory=utc_now, sa_column=Column(UTCDateTime(), default=utc_now)
    )

    execution: Execution = Relationship(sa_relationship=relationship("Execution", back_populates="logs")
