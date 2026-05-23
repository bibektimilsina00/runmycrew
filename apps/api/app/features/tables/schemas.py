import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Field, SQLModel


class TableCreate(SQLModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


class TableSummaryOut(SQLModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    row_count: int
    column_count: int
    source: str
    owner: str
    created_at: datetime
    updated_at: datetime


class TableColumnCreate(SQLModel):
    name: str = Field(..., min_length=1, max_length=200)
    col_type: str = "text"
    options: dict[str, Any] | None = None


class TableColumnOut(SQLModel):
    id: uuid.UUID
    name: str
    col_type: str
    position: int
    options: dict[str, Any] | None = None


class TableRowUpsert(SQLModel):
    data: dict[str, Any]


class TableRowOut(SQLModel):
    id: uuid.UUID
    data: dict[str, Any]
    position: int | None = None


class TableRowsOut(SQLModel):
    columns: list[TableColumnOut]
    rows: list[TableRowOut]


class TableImportOut(TableSummaryOut):
    pass


class TableImportRowsOut(SQLModel):
    imported: int
