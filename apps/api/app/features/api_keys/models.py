from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship

from apps.api.app.shared.sqlmodel import SQLModelBase, utc_now

if TYPE_CHECKING:
    from apps.api.app.features.users.models import User


class ApiKey(SQLModelBase, table=True):
    """Developer API key model for authenticating CLI tools and services."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    name: str = Field(max_length=200)
    key_hash: str = Field(max_length=64, unique=True, index=True)
    key_preview: str = Field(max_length=50)
    created_at: datetime = Field(default_factory=utc_now)

    user: User = Relationship(sa_relationship=relationship("User", back_populates="api_keys"))
