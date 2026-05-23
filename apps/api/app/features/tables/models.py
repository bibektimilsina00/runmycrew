from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, Relationship
from sqlalchemy.orm import relationship

from apps.api.app.shared.sqlmodel import SQLModelBase, utc_now


class DataTable(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    user_id: uuid.UUID = Field(index=True)
    name: str = Field(max_length=200)
    description: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now, sa_column_kwargs={"onupdate": utc_now})

    columns: list["TableColumn"] = Relationship(sa_relationship=relationship("TableColumn", 
        back_populates="table",
        cascade="all, delete-orphan", order_by="TableColumn.position",)
    )
    rows: list["TableRow"] = Relationship(sa_relationship=relationship("TableRow", 
        back_populates="table", cascade="all, delete-orphan")
    )


class TableColumn(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    table_id: uuid.UUID = Field(foreign_key="datatable.id", ondelete="CASCADE", index=True)
    name: str = Field(max_length=200)
    col_type: str = Field(default="text", max_length=50)
    position: int = Field(default=0)
    options: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)

    table: DataTable = Relationship(id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    table_id: uuid.UUID = Field(foreign_key="datatable.id", ondelete="CASCADE", index=True)
    name: str = Field(max_length=200)
    col_type: str = Field(default="text", max_length=50)
    position: int = Field(default=0)
    options: dict[str, Any] = Relationship(sa_relationship=relationship("dict[str, Any]", back_populates="columns")


class TableRow(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    table_id: uuid.UUID = Field(foreign_key="datatable.id", ondelete="CASCADE", index=True)
    position: int = Field(default=0)
    data: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now, sa_column_kwargs={"onupdate": utc_now})

    table: DataTable = Relationship(sa_relationship=relationship("DataTable", back_populates="rows")
