import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship

from apps.api.app.shared.sqlmodel import (
    SQLModelBase,
    UTCDateTime,
    created_at_field,
    updated_at_field,
)

if TYPE_CHECKING:
    from apps.api.app.features.users.models import User


class Crew(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    description: str | None = Field(default=None)
    graph: dict[str, Any] = Field(
        default_factory=lambda: {"nodes": [], "edges": []},
        sa_column=Column(JSON, nullable=False, default=lambda: {"nodes": [], "edges": []}),
    )
    is_active: bool = Field(default=False)
    position: int = Field(default=0)
    color: str | None = Field(default=None, max_length=50)
    # Crew-level total-cost budget across all agent nodes in a single run.
    # 0 = unlimited (still bounded by per-agent Budget caps in agent.py).
    max_cost_usd: float = Field(default=0.0)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()

    user: "User" = Relationship()
    executions: list["CrewExecution"] = Relationship(
        back_populates="crew", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class CrewExecution(SQLModelBase, table=True):
    __tablename__ = "crew_execution"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    crew_id: uuid.UUID = Field(foreign_key="crew.id", ondelete="CASCADE", index=True)
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
    logs: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))

    crew: "Crew" = Relationship(back_populates="executions")
