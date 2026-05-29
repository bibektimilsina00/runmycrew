import time
import uuid
from typing import Any

import httpx
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.core.logger import get_logger
from apps.api.app.credential_manager.encryption.aes import AESEncryptionService
from apps.api.app.execution_engine.engine.node_executor import node_executor
from apps.api.app.features.credentials.service import CredentialService
from apps.api.app.features.nodes.schemas import NodeTestRequest, NodeTestResponse
from apps.api.app.features.secrets.repository import SecretRepository
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.registry.registry import node_registry

logger = get_logger(__name__)


class NodeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_nodes(self) -> list[dict[str, Any]]:
        """List all available nodes and their metadata."""
        return node_registry.list_nodes()

    async def test_node(
        self, body: NodeTestRequest, current_user: User, workspace: Workspace
    ) -> NodeTestResponse:
        credential_service = CredentialService(self.db)
        credentials = await credential_service.list_decrypted_for_workspace(workspace.id)

        secrets: dict[str, str] = {}

        _enc = AESEncryptionService()
        secret_repo = SecretRepository(self.db)
        secrets_list = await secret_repo.list_by_workspace(workspace.id, current_user.id)
        for s in secrets_list:
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
                db=self.db,
                emitter=None,
                run_downstream=None,
                pause=None,
            )
            context.__dict__["secrets"] = secrets

            start = time.time()
            result = await node_executor.execute_node(
                node_type=body.node_type,
                node_id="test-node",
                properties=body.properties,
                input_data=body.input_data,
                context=context,
            )
            duration_ms = int((time.time() - start) * 1000)

        return NodeTestResponse(
            success=result.success,
            output=result.output_data,
            error=result.error,
            logs=result.logs,
            duration_ms=duration_ms,
        )


def get_node_service(db: AsyncSession = Depends(get_db)) -> NodeService:
    return NodeService(db)
