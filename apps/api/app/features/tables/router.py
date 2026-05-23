import io
import uuid

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from fastapi.responses import StreamingResponse

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
from apps.api.app.features.tables.service import TableService, get_table_service
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

router = APIRouter()


# ── Tables CRUD ───────────────────────────────────────────────────────────────


@router.get("/", response_model=list[TableSummaryOut])
async def list_tables(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: TableService = Depends(get_table_service),
):
    return await service.list_tables(current_user, workspace)


@router.post("/", response_model=TableSummaryOut, status_code=status.HTTP_201_CREATED)
async def create_table(
    body: TableCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: TableService = Depends(get_table_service),
):
    return await service.create_table(body, current_user, workspace)


@router.post("/import.csv", response_model=TableImportOut, status_code=status.HTTP_201_CREATED)
async def import_csv_as_table(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: TableService = Depends(get_table_service),
):
    content = (await file.read()).decode("utf-8", errors="replace")
    filename = file.filename or "import.csv"
    return await service.import_csv_as_table(filename, content, current_user, workspace)


@router.delete("/{table_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_table(
    table_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    service: TableService = Depends(get_table_service),
):
    await service.delete_table(table_id, workspace)


# ── Columns ───────────────────────────────────────────────────────────────────


@router.post(
    "/{table_id}/columns", response_model=TableColumnOut, status_code=status.HTTP_201_CREATED
)
async def add_column(
    table_id: uuid.UUID,
    body: TableColumnCreate,
    workspace: Workspace = Depends(get_current_workspace),
    service: TableService = Depends(get_table_service),
):
    return await service.add_column(table_id, body, workspace)


@router.patch("/{table_id}/columns/{column_id}", response_model=TableColumnOut)
async def update_column(
    table_id: uuid.UUID,
    column_id: uuid.UUID,
    body: TableColumnCreate,
    workspace: Workspace = Depends(get_current_workspace),
    service: TableService = Depends(get_table_service),
):
    return await service.update_column(table_id, column_id, body, workspace)


@router.delete(
    "/{table_id}/columns/{column_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_column(
    table_id: uuid.UUID,
    column_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    service: TableService = Depends(get_table_service),
):
    await service.delete_column(table_id, column_id, workspace)


# ── Rows ──────────────────────────────────────────────────────────────────────


@router.get("/{table_id}/rows", response_model=TableRowsOut)
async def list_rows(
    table_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    service: TableService = Depends(get_table_service),
):
    return await service.list_rows(table_id, workspace)


@router.post("/{table_id}/rows", response_model=TableRowOut, status_code=status.HTTP_201_CREATED)
async def add_row(
    table_id: uuid.UUID,
    body: TableRowUpsert | None = None,
    workspace: Workspace = Depends(get_current_workspace),
    service: TableService = Depends(get_table_service),
):
    return await service.add_row(table_id, body, workspace)


@router.patch("/{table_id}/rows/{row_id}", response_model=TableRowOut)
async def update_row(
    table_id: uuid.UUID,
    row_id: uuid.UUID,
    body: TableRowUpsert,
    workspace: Workspace = Depends(get_current_workspace),
    service: TableService = Depends(get_table_service),
):
    return await service.update_row(table_id, row_id, body, workspace)


@router.delete(
    "/{table_id}/rows/{row_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_row(
    table_id: uuid.UUID,
    row_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    service: TableService = Depends(get_table_service),
):
    await service.delete_row(table_id, row_id, workspace)


# ── CSV Import / Export ───────────────────────────────────────────────────────


@router.get("/{table_id}/export.csv")
async def export_csv(
    table_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    service: TableService = Depends(get_table_service),
):
    csv_str, table_name = await service.export_csv(table_id, workspace)
    return StreamingResponse(
        io.StringIO(csv_str),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{table_name}.csv"'},
    )


@router.post(
    "/{table_id}/import.csv", response_model=TableImportRowsOut, status_code=status.HTTP_201_CREATED
)
async def import_csv(
    table_id: uuid.UUID,
    file: UploadFile = File(...),
    workspace: Workspace = Depends(get_current_workspace),
    service: TableService = Depends(get_table_service),
):
    content = (await file.read()).decode("utf-8", errors="replace")
    return await service.import_csv(table_id, content, workspace)
