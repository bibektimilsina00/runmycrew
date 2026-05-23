from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship

from apps.api.app.shared.sqlmodel import SQLModelBase, utc_now

if TYPE_CHECKING:
    from apps.api.app.features.users.models import User
    from apps.api.app.features.workflows.models import Workflow


class Folder(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field()
    parent_id: uuid.UUID | None = Field(default=None, foreign_key="folder.id")
    user_id: uuid.UUID = Field(foreign_key="user.id")
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now, sa_column_kwargs={"onupdate": utc_now})

    user: User = Relationship(sa_relationship=relationship("User", back_populates="folders"))
    parent: Folder | None = Relationship(
        sa_relationship=relationship("Folder", back_populates="children", remote_side="Folder.id")
    )
    children: list[Folder] = Relationship(
        sa_relationship=relationship("Folder", back_populates="parent", cascade="all, delete-orphan")
    )
    workflows: list[Workflow] = Relationship(
        sa_relationship=relationship("Workflow", back_populates="folder", cascade="all, delete-orphan")
    )
