import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.features.tables.models import DataTable, TableColumn, TableRow


class TableRepository:
    """Repository for handling database operations on DataTable, TableColumn, and TableRow models."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_table_by_id(
        self, table_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> DataTable | None:
        """Retrieve a DataTable by ID within a workspace, preloading columns."""
        result = await self.db.execute(
            sa.select(DataTable)
            .where(DataTable.id == table_id, DataTable.workspace_id == workspace_id)
            .options(selectinload(DataTable.columns))
        )
        return result.scalar_one_or_none()

    async def list_tables_summary(
        self, workspace_id: uuid.UUID
    ) -> list[tuple[DataTable, int, int]]:
        """List tables in a workspace along with row and column counts."""
        row_counts = (
            sa.select(TableRow.table_id, sa.func.count(TableRow.id).label("row_count"))
            .group_by(TableRow.table_id)
            .subquery()
        )
        col_counts = (
            sa.select(TableColumn.table_id, sa.func.count(TableColumn.id).label("column_count"))
            .group_by(TableColumn.table_id)
            .subquery()
        )
        result = await self.db.execute(
            sa.select(
                DataTable,
                sa.func.coalesce(row_counts.c.row_count, 0),
                sa.func.coalesce(col_counts.c.column_count, 0),
            )
            .outerjoin(row_counts, row_counts.c.table_id == DataTable.id)
            .outerjoin(col_counts, col_counts.c.table_id == DataTable.id)
            .where(DataTable.workspace_id == workspace_id)
            .order_by(DataTable.name)
        )
        return list(result.all())

    async def create_table(self, table: DataTable, default_column: TableColumn) -> DataTable:
        """Create a table with a default column."""
        self.db.add(table)
        await self.db.flush()
        default_column.table_id = table.id
        self.db.add(default_column)
        await self.db.commit()
        await self.db.refresh(table)
        return table

    async def delete_table(self, table: DataTable) -> None:
        """Delete a table."""
        await self.db.delete(table)
        await self.db.commit()

    async def get_column_count(self, table_id: uuid.UUID) -> int:
        """Get total columns for a table."""
        count_r = await self.db.execute(
            sa.select(sa.func.count(TableColumn.id)).where(TableColumn.table_id == table_id)
        )
        return count_r.scalar() or 0

    async def get_row_count(self, table_id: uuid.UUID) -> int:
        """Get total rows for a table."""
        count_r = await self.db.execute(
            sa.select(sa.func.count(TableRow.id)).where(TableRow.table_id == table_id)
        )
        return count_r.scalar() or 0

    async def get_column(self, column_id: uuid.UUID, table_id: uuid.UUID) -> TableColumn | None:
        """Retrieve a column by ID and table ID."""
        r = await self.db.execute(
            sa.select(TableColumn).where(
                TableColumn.id == column_id, TableColumn.table_id == table_id
            )
        )
        return r.scalar_one_or_none()

    async def list_rows(self, table_id: uuid.UUID) -> list[TableRow]:
        """List rows for a table, sorted by position and creation time."""
        r = await self.db.execute(
            sa.select(TableRow)
            .where(TableRow.table_id == table_id)
            .order_by(TableRow.position, TableRow.created_at)
        )
        return list(r.scalars().all())

    async def get_row(self, row_id: uuid.UUID, table_id: uuid.UUID) -> TableRow | None:
        """Retrieve a row by ID and table ID."""
        r = await self.db.execute(
            sa.select(TableRow).where(TableRow.id == row_id, TableRow.table_id == table_id)
        )
        return r.scalar_one_or_none()

    async def add(self, obj: Any) -> None:
        """Add an object to the session tracking."""
        self.db.add(obj)

    async def flush(self) -> None:
        """Flush changes to the database."""
        await self.db.flush()

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.db.commit()

    async def refresh(self, obj: Any) -> None:
        """Refresh the state of an object from the database."""
        await self.db.refresh(obj)
