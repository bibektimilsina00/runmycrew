import uuid
from datetime import datetime
from typing import Any

from sqlmodel import SQLModel


class ExecutionLogOut(SQLModel):
    id: uuid.UUID
    node_id: str | None
    level: str
    message: str
    payload: dict[str, Any] | None
    timestamp: datetime


class ExecutionOut(SQLModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    status: str
    trigger_type: str
    input_data: dict[str, Any] | None
    output_data: dict[str, Any] | None
    started_at: datetime | None
    finished_at: datetime | None
    logs: list[ExecutionLogOut] = []


class ExecutionCreate(SQLModel):
    trigger_type: str = "manual"
    input_data: dict[str, Any] | None = None


class ResumeRequest(SQLModel):
    token: str
    input: dict[str, Any] = {}


class ExecutionRerunResponse(SQLModel):
    execution_id: str
    workflow_id: str


class ExecutionListItem(SQLModel):
    id: str
    workflow_id: str
    workflow_name: str
    workflow_color: str
    status: str
    trigger_type: str
    started_at: str | None
    finished_at: str | None
    duration_ms: int | None


class ExecutionListAllResponse(SQLModel):
    executions: list[ExecutionListItem]
    total: int
    limit: int
    offset: int


class ExecutionCancelResponse(SQLModel):
    status: str


class ExecutionResumeResponse(SQLModel):
    status: str
    execution_id: str
