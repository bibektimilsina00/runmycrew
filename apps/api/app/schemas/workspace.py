import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

WorkspaceRole = Literal["owner", "admin", "member", "viewer"]


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class WorkspaceOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    owner_id: uuid.UUID
    is_personal: bool
    avatar_url: str | None = None
    plan: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkspaceWithRoleOut(WorkspaceOut):
    role: WorkspaceRole
    member_count: int


class WorkspaceUserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class WorkspaceMemberOut(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: WorkspaceRole
    invited_by: uuid.UUID | None = None
    joined_at: datetime
    user: WorkspaceUserOut

    model_config = ConfigDict(from_attributes=True)


class WorkspaceInviteCreate(BaseModel):
    email: EmailStr
    role: WorkspaceRole = "member"
    send_email: bool = False


class WorkspaceInviteOut(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    email: EmailStr
    role: WorkspaceRole
    token: str
    invite_url: str
    expires_at: datetime
    accepted_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkspaceInvitePreviewOut(BaseModel):
    workspace_id: uuid.UUID
    workspace_name: str
    email: EmailStr
    role: WorkspaceRole
    expires_at: datetime
    accepted_at: datetime | None = None


class WorkspaceMemberUpdate(BaseModel):
    role: WorkspaceRole
