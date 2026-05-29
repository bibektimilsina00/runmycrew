import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from apps.api.app.shared.sqlmodel import SQLModelBase, created_at_field, updated_at_field

if TYPE_CHECKING:
    from apps.api.app.features.users.models import User


class Skill(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    name: str = Field(max_length=64)
    description: str = Field(default="", max_length=1024)
    icon: str = Field(default="BookOpen", max_length=64)
    color: str = Field(default="#8b5cf6", max_length=32)
    content: str = Field()
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()

    user: "User" = Relationship(back_populates="skills")
