import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.app.models.base import Base


def _now() -> datetime:
    return datetime.now(UTC)


class DataTable(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    columns: Mapped[list["TableColumn"]] = relationship("TableColumn", back_populates="table", cascade="all, delete-orphan", order_by="TableColumn.position")
    rows: Mapped[list["TableRow"]] = relationship("TableRow", back_populates="table", cascade="all, delete-orphan")


class TableColumn(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("datatable.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    col_type: Mapped[str] = mapped_column(String(50), default="text")  # text | number | boolean | date | select
    position: Mapped[int] = mapped_column(Integer, default=0)
    options: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # for select: {"choices": ["a","b"]}
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    table: Mapped["DataTable"] = relationship("DataTable", back_populates="columns")


class TableRow(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("datatable.id", ondelete="CASCADE"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)  # {column_id: value}
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    table: Mapped["DataTable"] = relationship("DataTable", back_populates="rows")
