import hashlib
import hmac
import json
import secrets
import uuid as _uuid
from datetime import UTC, datetime

from croniter import croniter
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.config import settings
from apps.api.app.core.database import get_db
from apps.api.app.core.logger import get_logger
from apps.api.app.execution_engine.engine import execution_engine
from apps.api.app.features.triggers.schemas import (
    CronNextRunsResponse,
    CronValidateRequest,
    CronValidateResponse,
    WebhookGithubReceiveResponse,
    WebhookInfoResponse,
    WebhookReceiveResponse,
    WebhookSecretResponse,
)
from apps.api.app.features.workflows.repository import WorkflowRepository
from apps.api.app.features.workflows.service import WorkflowService

logger = get_logger(__name__)


def verify_signature(raw_body: bytes, secret: str, signature_header: str) -> bool:
    computed = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    received = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(computed, received)


def find_webhook_node_props(workflow, path: str) -> dict | None:
    for node in workflow.graph.get("nodes", []):
        if node.get("type") == "trigger.webhook":
            props = node.get("data", {}).get("properties", {})
            if props.get("path") == path:
                return props
    return None


class TriggerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def validate_cron(self, body: CronValidateRequest) -> CronValidateResponse:
        expr = body.expression.strip()
        if not croniter.is_valid(expr):
            raise HTTPException(status_code=400, detail=f"Invalid cron expression: '{expr}'")

        now = datetime.now(UTC)
        citer = croniter(expr, now)
        next_runs = [citer.get_next(datetime).isoformat() for _ in range(min(body.count, 10))]

        return CronValidateResponse(
            valid=True,
            expression=expr,
            next_runs=next_runs,
        )

    def get_next_runs(self, expression: str, count: int) -> CronNextRunsResponse:
        expr = expression.strip()
        if not croniter.is_valid(expr):
            raise HTTPException(status_code=400, detail=f"Invalid cron expression: '{expr}'")

        now = datetime.now(UTC)
        citer = croniter(expr, now)
        next_runs = [citer.get_next(datetime).isoformat() for _ in range(count)]

        return CronNextRunsResponse(expression=expr, next_runs=next_runs)

    def generate_webhook_secret(self) -> WebhookSecretResponse:
        return WebhookSecretResponse(secret=secrets.token_hex(32))

    async def get_webhook_info(self, path: str) -> WebhookInfoResponse:
        service = WorkflowService(self.db)
        workflows = await service.repository.find_by_trigger_type(
            "trigger.webhook", property_filters={"path": path}
        )
        return WebhookInfoResponse(
            path=path,
            webhook_url=f"{settings.BASE_URL}/api/v1/webhooks/{path}",
            active=len(workflows) > 0,
            workflow_count=len(workflows),
        )

    async def receive_webhook(
        self,
        path: str,
        raw_body: bytes,
        headers: dict[str, str],
        query_params: dict[str, str],
        method: str,
    ) -> WebhookReceiveResponse:
        service = WorkflowService(self.db)
        workflows = await service.repository.find_by_trigger_type(
            "trigger.webhook", property_filters={"path": path}
        )

        if not workflows:
            raise HTTPException(status_code=404, detail=f"No active webhook found for path: {path}")

        execution_ids = []
        for workflow in workflows:
            node_props = find_webhook_node_props(workflow, path)

            if node_props and node_props.get("require_signature"):
                secret = node_props.get("secret") or ""
                if not secret:
                    logger.warning(f"Webhook {path}: require_signature=true but no secret set")
                    raise HTTPException(
                        status_code=401, detail="Webhook secret not configured on this trigger"
                    )

                sig_header = headers.get(
                    "x-runmycrew-signature", headers.get("X-RunMyCrew-Signature", "")
                )
                if not sig_header:
                    raise HTTPException(
                        status_code=401, detail="Missing X-RunMyCrew-Signature header"
                    )

                if not verify_signature(raw_body, secret, sig_header):
                    logger.warning(f"Webhook {path}: invalid signature")
                    raise HTTPException(status_code=401, detail="Invalid signature")

            try:
                payload = json.loads(raw_body)
            except Exception:
                payload = {"raw": raw_body.decode("utf-8", errors="replace")}

            trigger_data = {
                "body": payload,
                "headers": headers,
                "query": query_params,
                "method": method,
                "path": path,
            }

            execution_id = await execution_engine.trigger_workflow(
                workflow_id=workflow.id,
                graph=workflow.graph,
                trigger_type="trigger.webhook",
                input_data=trigger_data,
            )
            execution_ids.append(str(execution_id))

        logger.info(f"Webhook {path}: triggered {len(execution_ids)} workflow(s)")
        return WebhookReceiveResponse(
            status="accepted",
            triggered_count=len(execution_ids),
            execution_ids=execution_ids,
        )

    async def receive_github_webhook(
        self,
        workflow_id: str,
        raw_body: bytes,
        headers: dict[str, str],
    ) -> WebhookGithubReceiveResponse:
        event_type = headers.get("x-github-event", headers.get("X-GitHub-Event", "unknown"))
        delivery_id = headers.get("x-github-delivery", headers.get("X-GitHub-Delivery", ""))

        try:
            wf_id = _uuid.UUID(str(workflow_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid workflow ID") from None

        wf_repo = WorkflowRepository(self.db)
        workflow = await wf_repo.get_by_id(wf_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Find the GitHub webhook trigger node. Each workflow gets at most one
        # `trigger.github_webhook` — its `secret` is the HMAC key and its
        # `event` field gates which deliveries fan out into an execution.
        node_props: dict | None = None
        for node in workflow.graph.get("nodes", []):
            if node.get("type") == "trigger.github_webhook":
                node_props = node.get("data", {}).get("properties", {})
                break
        if not node_props:
            raise HTTPException(
                status_code=404,
                detail="No GitHub webhook trigger node found on this workflow",
            )

        hub_sig = headers.get("x-hub-signature-256", headers.get("X-Hub-Signature-256", ""))
        secret = str(node_props.get("secret") or "")
        if not secret:
            raise HTTPException(
                status_code=401, detail="Webhook secret not configured on this workflow"
            )
        if not hub_sig:
            raise HTTPException(status_code=401, detail="Missing X-Hub-Signature-256 header")
        if not verify_signature(raw_body, secret, hub_sig):
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Event filter — short-circuit deliveries that don't match the
        # node's `event` selector. "*" forwards every event.
        wanted_event = str(node_props.get("event") or "*")
        if wanted_event and wanted_event != "*" and wanted_event != event_type:
            logger.info(
                "GitHub webhook [%s] dropped by event filter (wanted=%s) workflow=%s",
                event_type,
                wanted_event,
                workflow.id,
            )
            return WebhookGithubReceiveResponse(status="ignored", execution_id="", event=event_type)

        try:
            payload = json.loads(raw_body)
        except Exception:
            payload = {"raw": raw_body.decode("utf-8", errors="replace")}

        trigger_data = {
            "event": event_type,
            "delivery": delivery_id,
            "action": payload.get("action") if isinstance(payload, dict) else None,
            "body": payload,
            "headers": headers,
            "repository": (payload.get("repository") or {}).get("full_name")
            if isinstance(payload, dict)
            else None,
            "sender": (payload.get("sender") or {}).get("login")
            if isinstance(payload, dict)
            else None,
        }

        execution_id = await execution_engine.trigger_workflow(
            workflow_id=workflow.id,
            graph=workflow.graph,
            trigger_type="trigger.github_webhook",
            input_data=trigger_data,
        )

        logger.info(f"GitHub webhook [{event_type}] -> workflow {workflow.id}")
        return WebhookGithubReceiveResponse(
            status="accepted", execution_id=str(execution_id), event=event_type
        )


def get_trigger_service(db: AsyncSession = Depends(get_db)) -> TriggerService:
    return TriggerService(db)
