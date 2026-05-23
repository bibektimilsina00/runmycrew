from typing import Any

from sqlmodel import SQLModel


class A2ARequest(SQLModel):
    message: str = ""
    trigger_data: dict[str, Any] = {}
    input_data: dict[str, Any] | None = None


class A2AStatusResponse(SQLModel):
    execution_id: str
    status: str
    output: Any | None = None


class A2ACancelResponse(SQLModel):
    execution_id: str
    status: str
