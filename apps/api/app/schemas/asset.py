import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AssetSourceType = Literal["uploaded", "generated", "attachment"]


class AssetOut(BaseModel):
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

    model_config = ConfigDict(from_attributes=True)


class AssetUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class AssetStats(BaseModel):
    count: int
    total_size: int
