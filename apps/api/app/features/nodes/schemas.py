from typing import Any

from sqlmodel import SQLModel


class NodeTestRequest(SQLModel):
    node_type: str
    properties: dict[str, Any] = {}
    input_data: dict[str, Any] = {}
    workflow_id: str | None = None


class NodeTestResponse(SQLModel):
    success: bool
    output: dict[str, Any] | list[Any] | None = None
    error: str | None = None
    logs: list[dict[str, Any]] = []
    duration_ms: int
