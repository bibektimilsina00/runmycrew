from fastapi import APIRouter

from apps.api.app.api.v1.a2a.router import router as a2a_router
from apps.api.app.api.v1.ai.router import router as ai_router
from apps.api.app.api.v1.assets.router import router as assets_router
from apps.api.app.api.v1.auth.router import router as auth_router
from apps.api.app.api.v1.copilot.router import router as copilot_router
from apps.api.app.api.v1.credentials.router import router as credentials_router
from apps.api.app.api.v1.executions.router import router as executions_router
from apps.api.app.api.v1.folders.router import router as folders_router
from apps.api.app.api.v1.integrations.router import router as integrations_router
from apps.api.app.api.v1.knowledge.router import router as knowledge_router
from apps.api.app.api.v1.logs.router import router as logs_router
from apps.api.app.api.v1.nodes.router import router as nodes_router
from apps.api.app.api.v1.secrets.router import router as secrets_router
from apps.api.app.api.v1.skills.router import router as skills_router
from apps.api.app.api.v1.tables.router import router as tables_router
from apps.api.app.api.v1.triggers.cron_utils import router as cron_router
from apps.api.app.api.v1.triggers.webhook_handler import router as webhooks_router
from apps.api.app.api.v1.users.router import router as users_router
from apps.api.app.api.v1.websocket.router import router as websocket_router
from apps.api.app.api.v1.workflows.router import router as workflows_router
from apps.api.app.api.v1.workspaces.router import router as workspaces_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(workflows_router, prefix="/workflows", tags=["workflows"])
router.include_router(workspaces_router, prefix="/workspaces", tags=["workspaces"])
router.include_router(folders_router, prefix="/folders", tags=["folders"])
router.include_router(executions_router, prefix="/executions", tags=["executions"])
router.include_router(credentials_router, prefix="/credentials", tags=["credentials"])
router.include_router(integrations_router, prefix="/integrations", tags=["integrations"])
router.include_router(websocket_router, prefix="/ws", tags=["realtime"])
router.include_router(ai_router, prefix="/ai", tags=["ai"])
router.include_router(nodes_router, prefix="/nodes", tags=["nodes"])
router.include_router(assets_router, prefix="/assets", tags=["assets"])
router.include_router(skills_router, prefix="/skills", tags=["skills"])
router.include_router(a2a_router, prefix="/a2a", tags=["a2a"])
router.include_router(copilot_router, prefix="/copilot", tags=["copilot"])
router.include_router(webhooks_router)
router.include_router(cron_router)
router.include_router(knowledge_router, prefix="/kb", tags=["knowledge"])
router.include_router(secrets_router, prefix="/secrets", tags=["secrets"])
router.include_router(tables_router, prefix="/tables", tags=["tables"])
router.include_router(logs_router, prefix="/logs", tags=["logs"])
