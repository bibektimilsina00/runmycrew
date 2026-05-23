import uuid
from datetime import datetime
from typing import Literal

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

WorkspaceRole = Literal["owner", "admin", "member", "viewer"]


class WorkspaceCreate(SQLModel):
    name: str = Field(..., min_length=1, max_length=200)


class WorkspaceOut(SQLModel):
    id: uuid.UUID
    name: str
    slug: str
    owner_id: uuid.UUID
    is_personal: bool
    avatar_url: str | None = None
    plan: str
    created_at: datetime
    updated_at: datetime


class WorkspaceWithRoleOut(WorkspaceOut):
    role: WorkspaceRole
    member_count: int


class WorkspaceUserOut(SQLModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None
    avatar_url: str | None = None


class WorkspaceMemberOut(SQLModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: WorkspaceRole
    invited_by: uuid.UUID | None = None
    joined_at: datetime
    user: WorkspaceUserOut


class WorkspaceInviteCreate(SQLModel):
    email: EmailStr
    role: WorkspaceRole = "member"
    send_email: bool = False


class WorkspaceInviteOut(SQLModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    email: EmailStr
    role: WorkspaceRole
    token: str
    invite_url: str
    expires_at: datetime
    accepted_at: datetime | None = None
    created_at: datetime


class WorkspaceInvitePreviewOut(SQLModel):
    workspace_id: uuid.UUID
    workspace_name: str
    email: EmailStr
    role: WorkspaceRole
    expires_at: datetime
    accepted_at: datetime | None = None


class WorkspaceUpdate(SQLModel):
    name: str = Field(..., min_length=1, max_length=200)


class WorkspaceMemberUpdate(SQLModel):
    role: WorkspaceRole
