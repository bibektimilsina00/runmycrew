import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Field, SQLModel


class CrewCreate(SQLModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    position: int = 0
    color: str | None = None
    graph: dict[str, Any] = Field(default_factory=lambda: {"nodes": [], "edges": []})


class CrewUpdate(SQLModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    position: int | None = None
    graph: dict[str, Any] | None = None
    is_active: bool | None = None
    color: str | None = None


class CrewOut(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None
    graph: dict[str, Any]
    is_active: bool
    position: int
    color: str | None = None
    created_at: datetime
    updated_at: datetime


class CrewExecutionOut(SQLModel):
    id: uuid.UUID
    crew_id: uuid.UUID
    status: str
    trigger_type: str
    input_data: dict[str, Any] | None = None
    output_data: dict[str, Any] | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    snapshot: dict[str, Any] | None = None
    resume_token: str | None = None
    resume_schema: dict[str, Any] | None = None
    paused_node_id: str | None = None
    logs: dict[str, Any] | None = None
