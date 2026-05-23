from typing import Any

from fastapi import APIRouter, Depends

from apps.api.app.features.nodes.schemas import NodeTestRequest, NodeTestResponse
from apps.api.app.features.nodes.service import NodeService, get_node_service
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

router = APIRouter()


@router.get("/")
async def list_nodes(
    service: NodeService = Depends(get_node_service),
) -> list[dict[str, Any]]:
    """List all available nodes and their metadata."""
    return await service.list_nodes()


@router.post("/test", response_model=NodeTestResponse)
async def test_node(
    body: NodeTestRequest,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: NodeService = Depends(get_node_service),
):
    """Execute a single node with custom input — no full workflow run needed."""
    return await service.test_node(body, current_user, workspace)
