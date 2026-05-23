import uuid
from datetime import datetime

from sqlmodel import SQLModel


class FolderBase(SQLModel):
    name: str
    parent_id: uuid.UUID | None = None


class FolderCreate(FolderBase):
    pass


class FolderUpdate(SQLModel):
    name: str | None = None
    parent_id: uuid.UUID | None = None


class FolderOut(FolderBase):
    id: uuid.UUID
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class FolderDeleteResponse(SQLModel):
    status: str
