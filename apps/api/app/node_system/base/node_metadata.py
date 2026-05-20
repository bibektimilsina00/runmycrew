from typing import Any

from pydantic import BaseModel


class NodeMetadata(BaseModel):
    type: str
    name: str
    category: str
    description: str
    properties: list[dict[str, Any]]
    inputs: int
    outputs: int
    icon: str = "Circle"
    color: str = "#3b82f6"
    outputs_schema: list[dict[str, Any]] = []
    allow_error: bool = False
    credential_type: str | list[str] | None = None
    tools: list[str] | None = None
    operation_tool_map: dict[str, str] | None = None
