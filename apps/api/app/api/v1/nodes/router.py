import time
import uuid
from typing import Any

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.api.v1.workspaces.dependencies import get_current_workspace
from apps.api.app.core.database import get_db
from apps.api.app.core.logger import get_logger
from apps.api.app.models.user import User
from apps.api.app.models.workspace import Workspace
from apps.api.app.node_system.registry.registry import node_registry

router = APIRouter()
logger = get_logger(__name__)


@router.get("/")
async def list_nodes() -> list[dict[str, Any]]:
    """List all available nodes and their metadata."""
    return node_registry.list_nodes()


class NodeTestRequest(BaseModel):
    node_type: str
    properties: dict[str, Any] = {}
    input_data: dict[str, Any] = {}
    workflow_id: str | None = None


@router.post("/test")
async def test_node(
    body: NodeTestRequest,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Execute a single node with custom input — no full workflow run needed."""
    from apps.api.app.execution_engine.engine.node_executor import node_executor
    from apps.api.app.node_system.base.node_context import NodeContext
    from apps.api.app.services.credential_service import CredentialService

    credential_service = CredentialService(db)
    credentials = await credential_service.list_decrypted_for_workspace(workspace.id)

    # Load user secrets for {{secrets.KEY}} interpolation
    secrets: dict[str, str] = {}
    import sqlalchemy as sa

    from apps.api.app.credential_manager.encryption.aes import AESEncryptionService
    from apps.api.app.models.secret import Secret

    _enc = AESEncryptionService()
    result = await db.execute(sa.select(Secret).where(Secret.workspace_id == workspace.id))
    for s in result.scalars().all():
        try:
            secrets[s.name] = _enc.decrypt(s.encrypted_value)
        except Exception as exc:
            logger.warning("Failed to decrypt secret %s for node test: %s", s.id, exc)

    async with httpx.AsyncClient(timeout=120.0) as http_client:
        context = NodeContext(
            execution_id=f"test-{uuid.uuid4()}",
            workflow_id=body.workflow_id or "test",
            node_id="test-node",
            variables={},
            credentials=credentials,
            http_client=http_client,
            db=db,
            emitter=None,
            run_downstream=None,
            pause=None,
        )
        # Inject secrets so template resolver uses them
        context.__dict__['secrets'] = secrets

        start = time.time()
        result = await node_executor.execute_node(
            node_type=body.node_type,
            node_id="test-node",
            properties=body.properties,
            input_data=body.input_data,
            context=context,
        )
        duration_ms = int((time.time() - start) * 1000)

    return {
        "success": result.success,
        "output": result.output_data,
        "error": result.error,
        "logs": result.logs,
        "duration_ms": duration_ms,
    }
