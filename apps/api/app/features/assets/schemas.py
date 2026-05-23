import uuid
from datetime import datetime
from typing import Literal

from sqlmodel import Field, SQLModel

AssetSourceType = Literal["uploaded", "generated", "attachment"]


class AssetOut(SQLModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    name: str
    file_type: str
    file_size: int
    source_type: AssetSourceType
    created_at: datetime
    updated_at: datetime
    url: str
    download_url: str


class AssetUpdate(SQLModel):
    name: str = Field(..., min_length=1, max_length=255)


class AssetStats(SQLModel):
    count: int
    total_size: int
