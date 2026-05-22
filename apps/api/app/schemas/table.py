import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TableCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


class TableSummaryOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    row_count: int
    column_count: int
    source: str
    owner: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TableColumnCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    col_type: str = "text"
    options: dict[str, Any] | None = None


class TableColumnOut(BaseModel):
    id: uuid.UUID
    name: str
    col_type: str
    position: int
    options: dict[str, Any] | None = None


class TableRowUpsert(BaseModel):
    data: dict[str, Any]


class TableRowOut(BaseModel):
    id: uuid.UUID
    data: dict[str, Any]
    position: int | None = None


class TableRowsOut(BaseModel):
    columns: list[TableColumnOut]
    rows: list[TableRowOut]


class TableImportOut(TableSummaryOut):
    pass


class TableImportRowsOut(BaseModel):
    imported: int
