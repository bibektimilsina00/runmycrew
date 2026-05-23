import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Field, SQLModel


class WorkflowCreate(SQLModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    folder_id: uuid.UUID | None = None
    position: int = 0
    color: str | None = None
    graph: dict[str, Any] = Field(default_factory=lambda: {"nodes": [], "edges": []})
    env: dict[str, str] | None = None


class WorkflowUpdate(SQLModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    folder_id: uuid.UUID | None = None
    position: int | None = None
    graph: dict[str, Any] | None = None
    is_active: bool | None = None
    color: str | None = None
    env: dict[str, str] | None = None
    expected_version: int | None = None


class WorkflowBatchItem(SQLModel):
    id: uuid.UUID
    folder_id: uuid.UUID | None = None
    position: int | None = None
    color: str | None = None


class WorkflowBatchUpdate(SQLModel):
    updates: list[WorkflowBatchItem]


class WorkflowOut(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    folder_id: uuid.UUID | None = None
    name: str
    description: str | None
    schema_version: str
    graph: dict[str, Any]
    is_active: bool
    position: int
    color: str | None = None
    env: dict[str, str] | None = None
    version_vector: int = 0
    created_at: datetime
    updated_at: datetime
