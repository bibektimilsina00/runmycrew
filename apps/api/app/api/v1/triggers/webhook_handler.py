import hashlib
import hmac
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.core.config import settings
from apps.api.app.core.database import get_db
from apps.api.app.core.logger import get_logger
from apps.api.app.models.user import User
from apps.api.app.services.workflow_service import WorkflowService

logger = get_logger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _verify_signature(raw_body: bytes, secret: str, signature_header: str) -> bool:
    computed = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    received = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(computed, received)


def _find_webhook_node_props(workflow, path: str) -> dict | None:
    for node in workflow.graph.get("nodes", []):
        if node.get("type") == "trigger.webhook":
            props = node.get("data", {}).get("properties", {})
            if props.get("path") == path:
                return props
    return None


@router.post("/utils/generate-secret")
async def generate_webhook_secret(
    current_user: User = Depends(get_current_user),
):
    """Generate a cryptographically secure webhook signing secret."""
    return {"secret": secrets.token_hex(32)}


@router.get("/{path}/info")
async def get_webhook_info(
    path: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns webhook URL and whether a workflow is listening on this path."""
    service = WorkflowService(db)
    workflows = await service.repository.find_by_trigger_type(
        "trigger.webhook", property_filters={"path": path}
    )
    return {
        "path": path,
        "webhook_url": f"{settings.BASE_URL}/api/v1/webhooks/{path}",
        "active": len(workflows) > 0,
        "workflow_count": len(workflows),
    }


@router.post("/{path}")
async def receive_webhook(
    path: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    raw_body = await request.body()

    service = WorkflowService(db)
    workflows = await service.repository.find_by_trigger_type(
        "trigger.webhook", property_filters={"path": path}
    )

    if not workflows:
        raise HTTPException(status_code=404, detail=f"No active webhook found for path: {path}")

    execution_ids = []
    for workflow in workflows:
        node_props = _find_webhook_node_props(workflow, path)

        if node_props and node_props.get("require_signature"):
            secret = node_props.get("secret") or ""
            if not secret:
                logger.warning(f"Webhook {path}: require_signature=true but no secret set")
                raise HTTPException(status_code=401, detail="Webhook secret not configured on this trigger")

            sig_header = request.headers.get("X-Fuse-Signature", "")
            if not sig_header:
                raise HTTPException(status_code=401, detail="Missing X-Fuse-Signature header")

            if not _verify_signature(raw_body, secret, sig_header):
                logger.warning(f"Webhook {path}: invalid signature")
                raise HTTPException(status_code=401, detail="Invalid signature")

        try:
            import json
            payload = json.loads(raw_body)
        except Exception:
            payload = {"raw": raw_body.decode("utf-8", errors="replace")}

        trigger_data = {
            "body": payload,
            "headers": dict(request.headers),
            "query": dict(request.query_params),
            "method": request.method,
            "path": path,
        }

        from apps.api.app.execution_engine.engine import execution_engine

        execution_id = await execution_engine.trigger_workflow(
            workflow_id=workflow.id,
            graph=workflow.graph,
            trigger_type="trigger.webhook",
            input_data=trigger_data,
        )
        execution_ids.append(str(execution_id))

    logger.info(f"Webhook {path}: triggered {len(execution_ids)} workflow(s)")
    return {
        "status": "accepted",
        "triggered_count": len(execution_ids),
        "execution_ids": execution_ids,
    }
