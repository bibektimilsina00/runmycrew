import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FolderBase(BaseModel):
    name: str
    parent_id: uuid.UUID | None = None


class FolderCreate(FolderBase):
    pass


class FolderUpdate(BaseModel):
    name: str | None = None
    parent_id: uuid.UUID | None = None


class FolderOut(FolderBase):
    id: uuid.UUID
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
