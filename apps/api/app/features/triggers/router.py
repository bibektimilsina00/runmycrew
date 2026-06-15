import json
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.core.logger import get_logger
from apps.api.app.core.redis import get_redis
from apps.api.app.features.executions.models import Execution
from apps.api.app.features.executions.repository import ExecutionRepository
from apps.api.app.features.triggers.listen_service import (
    DEFAULT_TTL_SECONDS,
    ListenSlot,
    close_slot,
    expected_event_label,
    find_slot,
    open_slot,
)
from apps.api.app.features.triggers.repository import TriggerFixtureRepository
from apps.api.app.features.triggers.schemas import (
    CronNextRunsResponse,
    CronValidateRequest,
    CronValidateResponse,
    TriggerFixtureResponse,
    TriggerListenRequest,
    TriggerListenResponse,
    TriggerListenStatusResponse,
    WebhookGithubReceiveResponse,
    WebhookInfoResponse,
    WebhookReceiveResponse,
    WebhookSecretResponse,
)
from apps.api.app.features.triggers.service import TriggerService, get_trigger_service
from apps.api.app.features.users.models import User
from apps.api.app.features.workflows.repository import WorkflowRepository
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

router = APIRouter()
logger = get_logger(__name__)


def _resolve_meta_trigger_slot(
    graph: dict | None,
    requested_node_id: str | None,
) -> dict[str, Any]:
    """Pick the Meta trigger node to listen on + lift its routing tuple.

    Returns a dict with keys: node_id, object_type, target_id, field,
    credential_id. Raises HTTPException(400) when no compatible trigger
    is found or when the user-specified `node_id` is missing.
    """
    # Lazy import to dodge the workflow → triggers import edge.
    from apps.api.app.features.meta.service import _EVENT_TO_FIELD, _TRIGGER_SPECS

    nodes = (graph or {}).get("nodes") or []
    candidates: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_type = str(node.get("type") or "")
        spec = _TRIGGER_SPECS.get(node_type)
        if spec is None:
            continue
        candidates.append({"node": node, "node_type": node_type, "spec": spec})

    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Workflow has no Meta trigger node to listen on. Add an "
                "Instagram / Facebook / WhatsApp / Lead Ads trigger first."
            ),
        )

    picked: dict[str, Any] | None = None
    if requested_node_id:
        for c in candidates:
            if str(c["node"].get("id") or "") == requested_node_id:
                picked = c
                break
        if picked is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Node id {requested_node_id!r} is not a Meta trigger in this workflow.",
            )
    else:
        if len(candidates) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow has multiple Meta triggers — pass node_id in the body to pick one.",
            )
        picked = candidates[0]

    node = picked["node"]
    spec = picked["spec"]
    node_type = picked["node_type"]
    props = (node.get("data") or {}).get("properties") or {}
    event_type = str(props.get("event_type") or "").strip()
    event_map = _EVENT_TO_FIELD.get(node_type) or {}
    if not event_type or event_type not in event_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Trigger node has no event_type set yet. Configure the trigger "
                "before clicking Listen."
            ),
        )
    object_type, field = event_map[event_type]
    target_id = str(props.get(spec["target_prop"]) or "").strip()
    if not target_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Trigger node is missing {spec['target_prop']!r}. Pick the "
                "target resource (Page / IG account / WABA) first."
            ),
        )
    credential_id = str(props.get("credential") or "").strip()
    if not credential_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Trigger node is missing 'credential'. Pick a Meta or "
                "Instagram credential before clicking Listen."
            ),
        )
    return {
        "node_id": str(node.get("id") or ""),
        "object_type": object_type,
        "target_id": target_id,
        "field": field,
        "credential_id": credential_id,
    }


@router.post(
    "/workflows/{workflow_id}/listen",
    tags=["triggers"],
    response_model=TriggerListenResponse,
)
async def listen_workflow(
    workflow_id: uuid.UUID,
    body: TriggerListenRequest | None = None,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Open a single-shot listen slot for the workflow's Meta trigger.

    Mirrors n8n's "Listen for test event" UX:

      - Editor calls this instead of `/run` when the user wants to
        verify the live webhook flow without activating the workflow.
      - A Redis-backed slot is keyed on `(object_type, target_id, field)`.
        The next webhook delivery matching that tuple fires the
        execution exactly once and closes the slot.
      - The execution row is created up front (status='waiting') so the
        editor's WS subscription can attach immediately and watch for
        `execution_waiting` → `node_started` → ... → terminal events.

    Slots TTL out after `DEFAULT_TTL_SECONDS` so a forgotten Listen
    doesn't hold state forever.
    """
    wf = await WorkflowRepository(db).get_by_id(workflow_id)
    if wf is None or wf.workspace_id != workspace.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    requested_node_id = body.node_id if body else None
    routing = _resolve_meta_trigger_slot(wf.graph, requested_node_id)

    # Make sure Meta is registered to deliver webhooks for this target —
    # otherwise the slot waits forever for an event Meta never sends.
    # subscribed_apps is idempotent so re-registering an active workflow
    # is a no-op. We DON'T persist a MetaSubscription row from here —
    # the listen slot is ephemeral; production routing still requires
    # explicit workflow activation.
    from apps.api.app.features.meta.service import register_meta_subscription

    try:
        await register_meta_subscription(
            db,
            credential_id=uuid.UUID(routing["credential_id"]),
            workspace_id=workspace.id,
            object_type=routing["object_type"],
            target_id=routing["target_id"],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Meta refused subscription: {exc}",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"register_meta_subscription failed for workflow {workflow_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Could not register webhook delivery with Meta. Check the "
                "credential's Meta App permissions and re-connect if needed."
            ),
        ) from exc

    # Messenger postback triggers also need a Get Started button installed
    # on the Page — without it the first tap on the conversation never
    # dispatches a `messaging_postback` event, leaving the listen slot
    # idle until TTL. Best-effort: a failure here logs but doesn't fail
    # /listen because Meta sometimes rejects the call for benign reasons
    # (already-installed payload, throttling) and we'd rather still open
    # the slot than block the user.
    if routing["object_type"] == "page" and routing["field"] == "messaging.postback":
        try:
            from apps.api.app.features.credentials.service import CredentialService
            from apps.api.app.features.meta.service import MetaService
            from apps.api.app.node_system.nodes.meta._helpers import page_token_by_page_id

            cred_service = CredentialService(db)
            cred = await cred_service.repo.get_by_id_and_workspace(
                uuid.UUID(routing["credential_id"]), workspace.id
            )
            if cred is not None:
                cred_data = await cred_service.get_decrypted_credential(cred)
                page_token = page_token_by_page_id(cred_data, routing["target_id"])
                if page_token:
                    await MetaService(db).register_messenger_get_started(
                        page_access_token=page_token,
                        page_id=routing["target_id"],
                    )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Messenger get_started auto-setup failed for workflow=%s page=%s: %s",
                workflow_id,
                routing["target_id"],
                exc,
            )

    execution = Execution(
        workflow_id=workflow_id,
        trigger_type="listen",
        status="waiting",
        input_data={},
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    execution_id = execution.id

    slot = ListenSlot(
        workflow_id=str(workflow_id),
        node_id=routing["node_id"],
        execution_id=str(execution_id),
        object_type=routing["object_type"],
        target_id=routing["target_id"],
        field=routing["field"],
        credential_id=routing["credential_id"],
    )
    await open_slot(slot)

    label = expected_event_label(routing["object_type"], routing["field"])

    # Publish a synthetic event so a WS already attached to this
    # execution flips to a "Waiting…" state without a round-trip GET.
    try:
        redis = await get_redis()
        await redis.publish(
            f"execution:{execution_id}",
            json.dumps(
                {
                    "type": "execution_waiting",
                    "execution_id": str(execution_id),
                    "node_id": routing["node_id"],
                    "waiting_for": label,
                    "target_id": routing["target_id"],
                    "ttl_seconds": DEFAULT_TTL_SECONDS,
                    "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                }
            ),
        )
    except Exception as exc:  # noqa: BLE001 — pubsub is best-effort
        logger.warning(f"Failed to publish execution_waiting for {execution_id}: {exc}")

    return TriggerListenResponse(
        execution_id=str(execution_id),
        node_id=routing["node_id"],
        waiting_for=label,
        target_id=routing["target_id"],
        ttl_seconds=DEFAULT_TTL_SECONDS,
    )


@router.post(
    "/workflows/{workflow_id}/triggers/{node_id}/listen/cancel",
    tags=["triggers"],
)
async def cancel_listen(
    workflow_id: uuid.UUID,
    node_id: str,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an open listen slot. Marks the held execution as cancelled
    and emits `execution_cancelled` so the editor WS terminates cleanly."""
    wf = await WorkflowRepository(db).get_by_id(workflow_id)
    if wf is None or wf.workspace_id != workspace.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    slot = await close_slot(str(workflow_id), node_id)
    if slot is None:
        return {"cancelled": False}

    try:
        await ExecutionRepository(db).update_status(uuid.UUID(slot.execution_id), "cancelled")
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Failed to mark execution {slot.execution_id} cancelled: {exc}")

    try:
        redis = await get_redis()
        await redis.publish(
            f"execution:{slot.execution_id}",
            json.dumps(
                {
                    "type": "execution_cancelled",
                    "execution_id": slot.execution_id,
                    "status": "cancelled",
                    "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                }
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Failed to publish execution_cancelled for {slot.execution_id}: {exc}")

    return {"cancelled": True, "execution_id": slot.execution_id}


@router.get(
    "/workflows/{workflow_id}/triggers/{node_id}/listen/status",
    tags=["triggers"],
    response_model=TriggerListenStatusResponse,
)
async def listen_status(
    workflow_id: uuid.UUID,
    node_id: str,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    wf = await WorkflowRepository(db).get_by_id(workflow_id)
    if wf is None or wf.workspace_id != workspace.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    slot = await find_slot(str(workflow_id), node_id)
    if slot is None:
        return TriggerListenStatusResponse(
            active=False, execution_id=None, waiting_for=None, target_id=None
        )
    return TriggerListenStatusResponse(
        active=True,
        execution_id=slot.execution_id,
        waiting_for=expected_event_label(slot.object_type, slot.field),
        target_id=slot.target_id,
    )


@router.get(
    "/workflows/{workflow_id}/triggers/{node_id}/fixture",
    tags=["triggers"],
    response_model=TriggerFixtureResponse,
)
async def get_trigger_fixture(
    workflow_id: uuid.UUID,
    node_id: str,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Read the last payload captured for a trigger node.

    Returns 404 when no event has ever fired this trigger — the editor
    surfaces that as "no captured event yet" so the user knows a manual
    Run can't replay anything until the trigger receives a real event.
    """
    wf = await WorkflowRepository(db).get_by_id(workflow_id)
    if wf is None or wf.workspace_id != workspace.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    fixture = await TriggerFixtureRepository(db).get(workflow_id, node_id)
    if fixture is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No captured event yet",
        )
    return TriggerFixtureResponse(
        node_id=fixture.node_id,
        source=fixture.source,
        captured_at=fixture.captured_at.isoformat(),
        payload=fixture.payload or {},
    )


@router.post("/cron/validate", tags=["cron"], response_model=CronValidateResponse)
async def validate_cron(
    body: CronValidateRequest,
    current_user: User = Depends(get_current_user),
    service: TriggerService = Depends(get_trigger_service),
):
    return service.validate_cron(body)


@router.get("/cron/next-runs", tags=["cron"], response_model=CronNextRunsResponse)
async def get_next_runs(
    expression: str = Query(...),
    count: int = Query(5, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    service: TriggerService = Depends(get_trigger_service),
):
    return service.get_next_runs(expression, count)


@router.post(
    "/webhooks/utils/generate-secret", tags=["webhooks"], response_model=WebhookSecretResponse
)
async def generate_webhook_secret(
    current_user: User = Depends(get_current_user),
    service: TriggerService = Depends(get_trigger_service),
):
    """Generate a cryptographically secure webhook signing secret."""
    return service.generate_webhook_secret()


@router.get("/webhooks/{path}/info", tags=["webhooks"], response_model=WebhookInfoResponse)
async def get_webhook_info(
    path: str,
    current_user: User = Depends(get_current_user),
    service: TriggerService = Depends(get_trigger_service),
):
    """Returns webhook URL and whether a workflow is listening on this path."""
    return await service.get_webhook_info(path)


@router.post("/webhooks/{path}", tags=["webhooks"], response_model=WebhookReceiveResponse)
async def receive_webhook(
    path: str,
    request: Request,
    service: TriggerService = Depends(get_trigger_service),
):
    raw_body = await request.body()
    return await service.receive_webhook(
        path=path,
        raw_body=raw_body,
        headers=dict(request.headers),
        query_params=dict(request.query_params),
        method=request.method,
    )


@router.post(
    "/webhooks/github/{workflow_id}", tags=["webhooks"], response_model=WebhookGithubReceiveResponse
)
async def receive_github_webhook(
    workflow_id: str,
    request: Request,
    service: TriggerService = Depends(get_trigger_service),
):
    """
    GitHub webhook endpoint scoped to a specific workflow.
    Set your GitHub webhook URL to: POST /api/v1/webhooks/github/{workflow_id}
    The workflow must have a trigger.webhook node with 'require_signature: true'
    and the signing secret matching the GitHub webhook secret.
    """
    raw_body = await request.body()
    return await service.receive_github_webhook(
        workflow_id=workflow_id,
        raw_body=raw_body,
        headers=dict(request.headers),
    )
