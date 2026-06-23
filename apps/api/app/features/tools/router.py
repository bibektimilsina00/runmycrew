"""FastAPI router for the tool catalog.

Auth-required (each endpoint depends on ``get_current_user``) so listing the
catalog stays scoped to authenticated users — same posture as the nodes
catalog. Filtering via query params; no body params today.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.app.features.tools.schemas import (
    McpProbeRequest,
    McpProbeResponse,
    ToolCategoryListResponse,
    ToolListResponse,
    ToolSchema,
)
from apps.api.app.features.tools.service import (
    McpProbeService,
    ToolCatalogService,
    WorkflowToolsService,
    get_mcp_probe_service,
    get_tool_catalog_service,
    get_workflow_tools_service,
)
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

router = APIRouter()


@router.get("/", response_model=ToolListResponse)
async def list_tools(
    q: str | None = None,
    category: str | None = None,
    requires_auth: bool | None = None,
    tag: str | None = None,
    dangerous: bool | None = None,
    _: User = Depends(get_current_user),
    service: ToolCatalogService = Depends(get_tool_catalog_service),
) -> ToolListResponse:
    """List every tool the agent node can pick from.

    Query params:
    - ``q`` — substring match across id / name / description / tags (case-insensitive).
    - ``category`` — filter by derived category bucket (e.g. ``slack``).
    - ``requires_auth`` — narrow to tools that do (or don't) need an OAuth credential.
    - ``tag`` — exact match on a single tag string (e.g. ``write``, ``read-only``).
    - ``dangerous`` — narrow to tools the registry has flagged as writes/deletes.
    """
    return service.list_tools(
        q=q,
        category=category,
        requires_auth=requires_auth,
        tag=tag,
        dangerous=dangerous,
    )


@router.get("/categories", response_model=ToolCategoryListResponse)
async def list_categories(
    _: User = Depends(get_current_user),
    service: ToolCatalogService = Depends(get_tool_catalog_service),
) -> ToolCategoryListResponse:
    """Distinct category buckets with counts."""
    return ToolCategoryListResponse(categories=service.list_categories())


@router.get("/workflows", response_model=ToolListResponse)
async def list_workflow_tools(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: WorkflowToolsService = Depends(get_workflow_tools_service),
) -> ToolListResponse:
    """List every workflow in this workspace as a callable tool.

    Each row is shaped like a built-in tool — id is ``workflow:<uuid>``,
    params are derived from the trigger node's ``input_schema``. The agent
    routes ``workflow:*`` execution through the same ``workflow_executor``
    machinery as the manual generic tool, just with the workflow id
    pre-bound from the saved entry.
    """
    return await service.list_for_user(current_user, workspace)


@router.post("/mcp/probe", response_model=McpProbeResponse)
async def probe_mcp_server(
    body: McpProbeRequest,
    _: User = Depends(get_current_user),
    service: McpProbeService = Depends(get_mcp_probe_service),
) -> McpProbeResponse:
    """Validate an MCP server URL and preview its discovered tool list.

    No persistence — this only round-trips to the server. The inspector
    calls it before / after saving the server entry so the user can
    confirm the connection works and see which tools the agent will pick
    up at run time.
    """
    return await service.probe(body.url, body.api_key)


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
