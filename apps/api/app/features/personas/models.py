import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship

from apps.api.app.shared.sqlmodel import (
    SQLModelBase,
    created_at_field,
    updated_at_field,
)

if TYPE_CHECKING:
    from apps.api.app.features.users.models import User


class Persona(SQLModelBase, table=True):
    """Reusable named agent: role + prompt + default tools/model.

    Overlays onto an ``action.agent`` node via ``persona_id``. Node-level
    props still win — persona is the default, not the lock.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    name: str = Field(max_length=255)
    role: str = Field(max_length=64)
    description: str | None = Field(default=None)
    system_prompt: str = Field(default="")
    default_provider: str | None = Field(default=None, max_length=64)
    default_model: str | None = Field(default=None, max_length=128)
    tools: list[Any] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False, default=list)
    )
    color: str | None = Field(default=None, max_length=50)
    icon_slug: str | None = Field(default=None, max_length=128)
    temperature: float = Field(default=0.3)
    max_iterations: int = Field(default=10)
    is_public: bool = Field(default=False, index=True)
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()

    user: "User" = Relationship()
