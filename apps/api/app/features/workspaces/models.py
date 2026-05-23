from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship

from apps.api.app.shared.sqlmodel import SQLModelBase, utc_now

if TYPE_CHECKING:
    from apps.api.app.features.users.models import User


class Workspace(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=200)
    slug: str = Field(max_length=100, unique=True, index=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    is_personal: bool = Field(default=False)
    avatar_url: str | None = Field(default=None, max_length=500)
    plan: str = Field(default="free", max_length=50)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now, sa_column_kwargs={"onupdate": utc_now})

    members: list[WorkspaceMember] = Relationship(sa_relationship=relationship("WorkspaceMember", 
        back_populates="workspace", cascade="all, delete-orphan")
    )
    invites: list[WorkspaceInvite] = Relationship(sa_relationship=relationship("WorkspaceInvite", 
        back_populates="workspace", cascade="all, delete-orphan")
    )


class WorkspaceMember(SQLModelBase, table=True):
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    role: str = Field(default="member", max_length=20)
    invited_by: uuid.UUID | None = Field(default=None, foreign_key="user.id", ondelete="SET NULL")
    joined_at: datetime = Field(default_factory=utc_now)

    workspace: Workspace = Relationship(sa_relationship=relationship("Workspace", back_populates="members"))
    user: User = Relationship(sa_relationship=relationship("User", back_populates="workspace_memberships"))


class WorkspaceInvite(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    email: str = Field(max_length=255, index=True)
    role: str = Field(default="member", max_length=20)
    token: str = Field(max_length=64, unique=True, index=True)
    invited_by: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    expires_at: datetime = Field()
    accepted_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)

    workspace: Workspace = Relationship(sa_relationship=relationship("Workspace", back_populates="invites"))

