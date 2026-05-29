import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, Relationship

from apps.api.app.shared.sqlmodel import SQLModelBase, created_at_field, updated_at_field


class DataTable(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    user_id: uuid.UUID = Field(index=True)
    name: str = Field(max_length=200)
    description: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()

    columns: list["TableColumn"] = Relationship(
        back_populates="table",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "order_by": "TableColumn.position",
        },
    )
    rows: list["TableRow"] = Relationship(
        back_populates="table", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class TableColumn(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    table_id: uuid.UUID = Field(foreign_key="datatable.id", ondelete="CASCADE", index=True)
    name: str = Field(max_length=200)
    col_type: str = Field(default="text", max_length=50)
    position: int = Field(default=0)
    options: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = created_at_field()

    table: "DataTable" = Relationship(back_populates="columns")


class TableRow(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    table_id: uuid.UUID = Field(foreign_key="datatable.id", ondelete="CASCADE", index=True)
    position: int = Field(default=0)
    data: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()

    table: "DataTable" = Relationship(back_populates="rows")
