import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship

from apps.api.app.shared.sqlmodel import SQLModelBase, UTCDateTime, utc_now

if TYPE_CHECKING:
    from apps.api.app.features.workflows.models import Workflow


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

    workflow: "Workflow" = Relationship(back_populates="executions")
    logs: list["ExecutionLog"] = Relationship(
        back_populates="execution", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


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

    execution: "Execution" = Relationship(back_populates="logs")
