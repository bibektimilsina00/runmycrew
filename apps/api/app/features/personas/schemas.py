import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Field, SQLModel


class PersonaCreate(SQLModel):
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1, max_length=64)
    description: str | None = None
    system_prompt: str = ""
    default_provider: str | None = None
    default_model: str | None = None
    tools: list[Any] = Field(default_factory=list)
    color: str | None = None
    icon_slug: str | None = None
    temperature: float = 0.3
    max_iterations: int = 10
    is_public: bool = False


class PersonaUpdate(SQLModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    role: str | None = Field(None, min_length=1, max_length=64)
    description: str | None = None
    system_prompt: str | None = None
    default_provider: str | None = None
    default_model: str | None = None
    tools: list[Any] | None = None
    color: str | None = None
    icon_slug: str | None = None
    temperature: float | None = None
    max_iterations: int | None = None
    is_public: bool | None = None


class PersonaOut(SQLModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    name: str
    role: str
    description: str | None
    system_prompt: str
    default_provider: str | None
    default_model: str | None
    tools: list[Any]
    color: str | None
    icon_slug: str | None
    temperature: float
    max_iterations: int
    is_public: bool
    created_at: datetime
    updated_at: datetime
