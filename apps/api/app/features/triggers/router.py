from fastapi import APIRouter, Depends, Query, Request

from apps.api.app.features.triggers.schemas import (
    CronNextRunsResponse,
    CronValidateRequest,
    CronValidateResponse,
    WebhookGithubReceiveResponse,
    WebhookInfoResponse,
    WebhookReceiveResponse,
    WebhookSecretResponse,
)
from apps.api.app.features.triggers.service import TriggerService, get_trigger_service
from apps.api.app.features.users.models import User
from apps.api.app.shared.dependencies import get_current_user

router = APIRouter()


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
