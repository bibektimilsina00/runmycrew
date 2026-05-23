from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Column
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship

from apps.api.app.shared.sqlmodel import SQLModelBase, utc_now

if TYPE_CHECKING:
    from apps.api.app.features.users.models import User


class AuditLog(SQLModelBase, table=True):
    """Immutable record of user actions on workspace resources."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    user_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", ondelete="SET NULL", index=True
    )
    action: str = Field(max_length=100, index=True)
    resource_type: str = Field(max_length=100)
    resource_id: str = Field(max_length=100)
    resource_name: str = Field(max_length=200)
    meta: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)

    user: User | None = Relationship(sa_relationship=relationship("User", lazy="joined"))
