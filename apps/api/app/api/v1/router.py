from fastapi import APIRouter

from apps.api.app.features.a2a.router import router as a2a_router
from apps.api.app.features.ai.router import router as ai_router
from apps.api.app.features.api_keys.router import router as api_keys_router
from apps.api.app.features.apps.owner_router import router as apps_owner_router
from apps.api.app.features.apps.public_router import router as apps_public_router
from apps.api.app.features.assets.router import router as assets_router
from apps.api.app.features.auth.router import router as auth_router
from apps.api.app.features.collaboration.websocket import router as collaboration_ws_router
from apps.api.app.features.copilot.router import router as copilot_router
from apps.api.app.features.credentials.router import router as credentials_router
from apps.api.app.features.crews.router import router as crews_router
from apps.api.app.features.dashboard.router import router as dashboard_router
from apps.api.app.features.escalation.router import router as escalation_router
from apps.api.app.features.executions.router import router as executions_router
from apps.api.app.features.executions.websocket import router as executions_ws_router
from apps.api.app.features.folders.router import router as folders_router
from apps.api.app.features.icons.router import router as icons_router
from apps.api.app.features.integrations.router import router as integrations_router
from apps.api.app.features.knowledge.router import router as knowledge_router
from apps.api.app.features.logs.router import router as logs_router
from apps.api.app.features.logs.websocket import router as logs_ws_router
from apps.api.app.features.meta.router import router as meta_router
from apps.api.app.features.nodes.router import router as nodes_router
from apps.api.app.features.personas.router import router as personas_router
from apps.api.app.features.secrets.router import router as secrets_router
from apps.api.app.features.skills.router import router as skills_router
from apps.api.app.features.tables.router import router as tables_router
from apps.api.app.features.templates.router import router as templates_router
from apps.api.app.features.tools.router import router as tools_router
from apps.api.app.features.triggers.router import router as triggers_router
from apps.api.app.features.users.router import router as users_router
from apps.api.app.features.webhooks.router import router as webhooks_router
from apps.api.app.features.workflows.router import router as workflows_router
from apps.api.app.features.workspaces.router import router as workspaces_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(api_keys_router, prefix="/api-keys", tags=["api-keys"])
router.include_router(workflows_router, prefix="/workflows", tags=["workflows"])
router.include_router(apps_owner_router, prefix="/workflows", tags=["apps"])
router.include_router(apps_public_router, prefix="/apps", tags=["apps"])
router.include_router(crews_router, prefix="/crews", tags=["crews"])
router.include_router(personas_router, prefix="/personas", tags=["personas"])
router.include_router(workspaces_router, prefix="/workspaces", tags=["workspaces"])
# Escalation config endpoints live under /workspaces/{id}/escalation-config —
# they're declared in their own feature module but mounted at the workspaces
# prefix so the URL reads naturally.
router.include_router(escalation_router, prefix="/workspaces", tags=["escalation"])
router.include_router(folders_router, prefix="/folders", tags=["folders"])
router.include_router(icons_router, prefix="/icons", tags=["icons"])
router.include_router(executions_router, prefix="/executions", tags=["executions"])
router.include_router(credentials_router, prefix="/credentials", tags=["credentials"])
router.include_router(integrations_router, prefix="/integrations", tags=["integrations"])
router.include_router(collaboration_ws_router, prefix="/ws", tags=["realtime"])
router.include_router(executions_ws_router, prefix="/ws", tags=["realtime"])
router.include_router(logs_ws_router, prefix="/ws", tags=["realtime"])
router.include_router(ai_router, prefix="/ai", tags=["ai"])
router.include_router(nodes_router, prefix="/nodes", tags=["nodes"])
router.include_router(assets_router, prefix="/assets", tags=["assets"])
router.include_router(skills_router, prefix="/skills", tags=["skills"])
router.include_router(a2a_router, prefix="/a2a", tags=["a2a"])
router.include_router(copilot_router, prefix="/copilot", tags=["copilot"])
router.include_router(triggers_router)
# Manifest-driven webhook receivers (gitlab, etc.) live under one
# provider-agnostic router. Adding a new webhook integration is a
# manifest file — no router edits needed.
router.include_router(webhooks_router)
router.include_router(meta_router)
router.include_router(knowledge_router, prefix="/kb", tags=["knowledge"])
router.include_router(secrets_router, prefix="/secrets", tags=["secrets"])
router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
router.include_router(tables_router, prefix="/tables", tags=["tables"])
router.include_router(logs_router, prefix="/logs", tags=["logs"])
router.include_router(tools_router, prefix="/tools", tags=["tools"])
router.include_router(templates_router, prefix="/templates", tags=["templates"])
