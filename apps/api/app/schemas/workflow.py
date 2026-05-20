import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    folder_id: uuid.UUID | None = None
    position: int = 0
    color: str | None = None
    graph: dict = Field(default_factory=lambda: {"nodes": [], "edges": []})
    env: dict[str, str] | None = None


class WorkflowUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    folder_id: uuid.UUID | None = None
    position: int | None = None
    graph: dict | None = None
    is_active: bool | None = None
    color: str | None = None
    env: dict[str, str] | None = None
    expected_version: int | None = None


class WorkflowBatchItem(BaseModel):
    id: uuid.UUID
    folder_id: uuid.UUID | None = None
    position: int | None = None
    color: str | None = None


class WorkflowBatchUpdate(BaseModel):
    updates: list[WorkflowBatchItem]


class WorkflowOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    folder_id: uuid.UUID | None = None
    name: str
    description: str | None
    schema_version: str
    graph: dict
    is_active: bool
    position: int
    color: str | None = None
    env: dict[str, str] | None = None
    version_vector: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
