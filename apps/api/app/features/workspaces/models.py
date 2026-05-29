import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, UniqueConstraint
from sqlmodel import Field, Relationship

from apps.api.app.shared.sqlmodel import (
    SQLModelBase,
    UTCDateTime,
    created_at_field,
    updated_at_field,
)

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
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()

    members: list["WorkspaceMember"] = Relationship(
        back_populates="workspace", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    invites: list["WorkspaceInvite"] = Relationship(
        back_populates="workspace", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class WorkspaceMember(SQLModelBase, table=True):
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    role: str = Field(default="member", max_length=20)
    invited_by: uuid.UUID | None = Field(default=None, foreign_key="user.id", ondelete="SET NULL")
    joined_at: datetime = created_at_field()

    workspace: "Workspace" = Relationship(back_populates="members")
    user: "User" = Relationship(
        back_populates="workspace_memberships",
        sa_relationship_kwargs={"foreign_keys": "[WorkspaceMember.user_id]"},
    )


class WorkspaceInvite(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    email: str = Field(max_length=255, index=True)
    role: str = Field(default="member", max_length=20)
    token: str = Field(max_length=64, unique=True, index=True)
    invited_by: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    expires_at: datetime = Field(sa_column=Column(UTCDateTime(), nullable=False))
    accepted_at: datetime | None = Field(default=None, sa_column=Column(UTCDateTime()))
    created_at: datetime = created_at_field()

    workspace: "Workspace" = Relationship(back_populates="invites")
