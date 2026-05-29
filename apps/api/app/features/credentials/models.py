import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlmodel import JSON, Field, Relationship

from apps.api.app.shared.sqlmodel import SQLModelBase, created_at_field, updated_at_field

if TYPE_CHECKING:
    from apps.api.app.features.users.models import User


class Credential(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    name: str = Field()
    type: str = Field()
    encrypted_data: str = Field()
    meta: dict[str, Any] | None = Field(default=None, sa_type=JSON)
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()

    user: "User" = Relationship(back_populates="credentials")
