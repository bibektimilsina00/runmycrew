"""FastAPI router for the tool catalog.

Auth-required (each endpoint depends on ``get_current_user``) so listing the
catalog stays scoped to authenticated users — same posture as the nodes
catalog. Filtering via query params; no body params today.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.app.features.tools.schemas import (
    ToolCategoryListResponse,
    ToolListResponse,
    ToolSchema,
)
from apps.api.app.features.tools.service import (
    ToolCatalogService,
    get_tool_catalog_service,
)
from apps.api.app.features.users.models import User
from apps.api.app.shared.dependencies import get_current_user

router = APIRouter()


@router.get("/", response_model=ToolListResponse)
async def list_tools(
    q: str | None = None,
    category: str | None = None,
    requires_auth: bool | None = None,
    _: User = Depends(get_current_user),
    service: ToolCatalogService = Depends(get_tool_catalog_service),
) -> ToolListResponse:
    """List every tool the agent node can pick from.

    Query params:
    - ``q`` — substring match across id / name / description (case-insensitive).
    - ``category`` — filter by derived category bucket (e.g. ``slack``).
    - ``requires_auth`` — narrow to tools that do (or don't) need an OAuth credential.
    """
    return service.list_tools(q=q, category=category, requires_auth=requires_auth)


@router.get("/categories", response_model=ToolCategoryListResponse)
async def list_categories(
    _: User = Depends(get_current_user),
    service: ToolCatalogService = Depends(get_tool_catalog_service),
) -> ToolCategoryListResponse:
    """Distinct category buckets with counts."""
    return ToolCategoryListResponse(categories=service.list_categories())


@router.get("/{tool_id}", response_model=ToolSchema)
async def get_tool(
    tool_id: str,
    _: User = Depends(get_current_user),
    service: ToolCatalogService = Depends(get_tool_catalog_service),
) -> ToolSchema:
    """Fetch a single tool by id, with versioned-alias resolution."""
    tool = service.get_tool(tool_id)
    if tool is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    return tool
