import csv
import io
import uuid

import sqlalchemy as sa
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.core.database import get_db
from apps.api.app.features.tables.models import DataTable, TableColumn, TableRow
from apps.api.app.features.tables.schemas import (
    TableColumnCreate,
    TableColumnOut,
    TableCreate,
    TableImportOut,
    TableImportRowsOut,
    TableRowOut,
    TableRowsOut,
    TableRowUpsert,
    TableSummaryOut,
)
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace


class TableService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _summary_out(
        self, table: DataTable, row_count: int, column_count: int, owner: User
    ) -> TableSummaryOut:
        return TableSummaryOut(
            id=table.id,
            name=table.name,
            description=table.description,
            row_count=row_count,
            column_count=column_count,
            source=table.description or "Manual table",
            owner=owner.full_name or owner.email,
            created_at=table.created_at,
            updated_at=table.updated_at,
        )

    async def _get_table(self, table_id: uuid.UUID, workspace_id: uuid.UUID) -> DataTable:
        result = await self.db.execute(
            sa.select(DataTable)
            .where(DataTable.id == table_id, DataTable.workspace_id == workspace_id)
            .options(selectinload(DataTable.columns))
        )
        t = result.scalar_one_or_none()
        if not t:
            raise HTTPException(status_code=404, detail="Table not found")
        return t

    async def list_tables(self, current_user: User, workspace: Workspace) -> list[TableSummaryOut]:
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
            .where(DataTable.workspace_id == workspace.id)
            .order_by(DataTable.name)
        )
        return [
            self._summary_out(t, int(row_count or 0), int(column_count or 0), current_user)
            for t, row_count, column_count in result.all()
        ]

    async def create_table(
        self, body: TableCreate, current_user: User, workspace: Workspace
    ) -> TableSummaryOut:
        table = DataTable(
            workspace_id=workspace.id,
            user_id=current_user.id,
            name=body.name.strip(),
            description=body.description,
        )
        self.db.add(table)
        await self.db.flush()
        col = TableColumn(table_id=table.id, name="name", col_type="text", position=0)
        self.db.add(col)
        await self.db.commit()
        await self.db.refresh(table)
        return self._summary_out(table, 0, 1, current_user)

    async def import_csv_as_table(
        self, filename: str, content: str, current_user: User, workspace: Workspace
    ) -> TableImportOut:
        table_name = filename.rsplit(".", 1)[0].strip() or "Imported table"
        table = DataTable(
            workspace_id=workspace.id,
            user_id=current_user.id,
            name=table_name[:200],
            description="CSV import",
        )
        self.db.add(table)
        await self.db.flush()

        reader = csv.DictReader(io.StringIO(content))
        headers = [header for header in (reader.fieldnames or []) if header]

        col_map: dict[str, str] = {}
        for position, header in enumerate(headers):
            col = TableColumn(
                table_id=table.id, name=header[:200], col_type="text", position=position
            )
            self.db.add(col)
            await self.db.flush()
            col_map[header] = str(col.id)

        row_count = 0
        for position, row in enumerate(reader):
            data = {col_map[key]: value for key, value in row.items() if key in col_map}
            self.db.add(TableRow(table_id=table.id, position=position, data=data))
            row_count += 1

        await self.db.commit()
        await self.db.refresh(table)
        return TableImportOut(
            **self._summary_out(table, row_count, len(headers), current_user).model_dump()
        )

    async def delete_table(self, table_id: uuid.UUID, workspace: Workspace) -> None:
        t = await self._get_table(table_id, workspace.id)
        await self.db.delete(t)
        await self.db.commit()

    async def add_column(
        self, table_id: uuid.UUID, body: TableColumnCreate, workspace: Workspace
    ) -> TableColumnOut:
        await self._get_table(table_id, workspace.id)
        count_r = await self.db.execute(
            sa.select(sa.func.count(TableColumn.id)).where(TableColumn.table_id == table_id)
        )
        pos = count_r.scalar() or 0
        col = TableColumn(
            table_id=table_id,
            name=body.name.strip(),
            col_type=body.col_type,
            position=pos,
            options=body.options,
        )
        self.db.add(col)
        await self.db.commit()
        await self.db.refresh(col)
        return TableColumnOut(
            id=col.id,
            name=col.name,
            col_type=col.col_type,
            position=col.position,
            options=col.options,
        )

    async def update_column(
        self,
        table_id: uuid.UUID,
        column_id: uuid.UUID,
        body: TableColumnCreate,
        workspace: Workspace,
    ) -> TableColumnOut:
        await self._get_table(table_id, workspace.id)
        r = await self.db.execute(
            sa.select(TableColumn).where(
                TableColumn.id == column_id, TableColumn.table_id == table_id
            )
        )
        col = r.scalar_one_or_none()
        if not col:
            raise HTTPException(404, "Column not found")
        col.name = body.name.strip()
        col.col_type = body.col_type
        col.options = body.options
        await self.db.commit()
        return TableColumnOut(
            id=col.id,
            name=col.name,
            col_type=col.col_type,
            position=col.position,
            options=col.options,
        )

    async def delete_column(
        self, table_id: uuid.UUID, column_id: uuid.UUID, workspace: Workspace
    ) -> None:
        await self._get_table(table_id, workspace.id)
        r = await self.db.execute(
            sa.select(TableColumn).where(
                TableColumn.id == column_id, TableColumn.table_id == table_id
            )
        )
        col = r.scalar_one_or_none()
        if not col:
            raise HTTPException(404, "Column not found")
        await self.db.delete(col)
        await self.db.commit()

    async def list_rows(self, table_id: uuid.UUID, workspace: Workspace) -> TableRowsOut:
        t = await self._get_table(table_id, workspace.id)
        r = await self.db.execute(
            sa.select(TableRow)
            .where(TableRow.table_id == table_id)
            .order_by(TableRow.position, TableRow.created_at)
        )
        rows = r.scalars().all()
        cols = [
            TableColumnOut(
                id=c.id,
                name=c.name,
                col_type=c.col_type,
                position=c.position,
                options=c.options,
            )
            for c in t.columns
        ]
        return TableRowsOut(
            columns=cols,
            rows=[TableRowOut(id=row.id, data=row.data, position=row.position) for row in rows],
        )

    async def add_row(
        self, table_id: uuid.UUID, body: TableRowUpsert | None, workspace: Workspace
    ) -> TableRowOut:
        await self._get_table(table_id, workspace.id)
        count_r = await self.db.execute(
            sa.select(sa.func.count(TableRow.id)).where(TableRow.table_id == table_id)
        )
        pos = count_r.scalar() or 0
        row = TableRow(table_id=table_id, position=pos, data=body.data if body else {})
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return TableRowOut(id=row.id, data=row.data, position=row.position)

    async def update_row(
        self, table_id: uuid.UUID, row_id: uuid.UUID, body: TableRowUpsert, workspace: Workspace
    ) -> TableRowOut:
        await self._get_table(table_id, workspace.id)
        r = await self.db.execute(
            sa.select(TableRow).where(TableRow.id == row_id, TableRow.table_id == table_id)
        )
        row = r.scalar_one_or_none()
        if not row:
            raise HTTPException(404, "Row not found")
        row.data = {**row.data, **body.data}
        await self.db.commit()
        return TableRowOut(id=row.id, data=row.data, position=row.position)

    async def delete_row(
        self, table_id: uuid.UUID, row_id: uuid.UUID, workspace: Workspace
    ) -> None:
        await self._get_table(table_id, workspace.id)
        r = await self.db.execute(
            sa.select(TableRow).where(TableRow.id == row_id, TableRow.table_id == table_id)
        )
        row = r.scalar_one_or_none()
        if not row:
            raise HTTPException(404, "Row not found")
        await self.db.delete(row)
        await self.db.commit()

    async def export_csv(self, table_id: uuid.UUID, workspace: Workspace) -> tuple[str, str]:
        t = await self._get_table(table_id, workspace.id)
        r = await self.db.execute(
            sa.select(TableRow).where(TableRow.table_id == table_id).order_by(TableRow.position)
        )
        rows = r.scalars().all()
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([c.name for c in t.columns])
        for row in rows:
            writer.writerow([row.data.get(str(c.id), "") for c in t.columns])
        return buf.getvalue(), t.name

    async def import_csv(
        self, table_id: uuid.UUID, content: str, workspace: Workspace
    ) -> TableImportRowsOut:
        t = await self._get_table(table_id, workspace.id)
        reader = csv.DictReader(io.StringIO(content))
        col_map = {c.name: str(c.id) for c in t.columns}

        for header in reader.fieldnames or []:
            if header not in col_map:
                count_r = await self.db.execute(
                    sa.select(sa.func.count(TableColumn.id)).where(TableColumn.table_id == table_id)
                )
                pos = count_r.scalar() or 0
                col = TableColumn(table_id=table_id, name=header, col_type="text", position=pos)
                self.db.add(col)
                await self.db.flush()
                col_map[header] = str(col.id)

        count_r = await self.db.execute(
            sa.select(sa.func.count(TableRow.id)).where(TableRow.table_id == table_id)
        )
        pos = count_r.scalar() or 0
        imported = 0
        for row in reader:
            data = {col_map[k]: v for k, v in row.items() if k in col_map}
            self.db.add(TableRow(table_id=t.id, position=pos, data=data))
            pos += 1
            imported += 1
        await self.db.commit()
        return TableImportRowsOut(imported=imported)


def get_table_service(db: AsyncSession = Depends(get_db)) -> TableService:
    return TableService(db)
