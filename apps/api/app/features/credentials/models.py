from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import relationship
from sqlmodel import JSON, Field, Relationship

from apps.api.app.shared.sqlmodel import SQLModelBase, utc_now

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
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now, sa_column_kwargs={"onupdate": utc_now})

    user: User = Relationship(sa_relationship=relationship("User", back_populates="credentials"))
