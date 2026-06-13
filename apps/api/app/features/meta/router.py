from __future__ import annotations

import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.config import settings
from apps.api.app.core.database import get_db
from apps.api.app.features.meta.schemas import (
    MetaResourcesResponse,
    MetaWebhookReceiveResponse,
)
from apps.api.app.features.meta.service import MetaService
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

router = APIRouter()


@router.get("/meta/resources", tags=["meta"], response_model=MetaResourcesResponse)
async def list_meta_resources(
    credential_id: _uuid.UUID = Query(...),
    kind: str = Query(..., description="page | ig_account | waba_phone | lead_form"),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    service = MetaService(db)
    resources = await service.list_resources(credential_id, kind, current_user, workspace)
    return MetaResourcesResponse(
        credential_id=str(credential_id),
        kind=kind,
        resources=resources,
    )


# Meta calls this once during webhook subscription with hub.mode=subscribe
# and an echo challenge. We respond with the challenge value as a *raw int*
# string if and only if the verify token matches. The endpoint is public
# (Meta can't send Bearer tokens) — the verify token is the shared secret.
@router.get("/webhooks/meta/{app_id}", tags=["meta-webhooks"])
async def verify_meta_webhook(
    app_id: str,
    request: Request,
):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode != "subscribe":
        raise HTTPException(status_code=400, detail="Unsupported hub.mode")
    if not settings.META_WEBHOOK_VERIFY_TOKEN or token != settings.META_WEBHOOK_VERIFY_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid verify token")
    # Meta expects the challenge echoed as a plain text response — not JSON.
    from fastapi.responses import PlainTextResponse

    return PlainTextResponse(challenge or "")


@router.post(
    "/webhooks/meta/{app_id}",
    tags=["meta-webhooks"],
    response_model=MetaWebhookReceiveResponse,
)
async def receive_meta_webhook(
    app_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    raw_body = await request.body()
    signature = request.headers.get("x-hub-signature-256") or request.headers.get(
        "X-Hub-Signature-256"
    )
    service = MetaService(db)
    triggered, execution_ids = await service.receive_webhook(app_id, raw_body, signature)
    return MetaWebhookReceiveResponse(
        status="accepted",
        triggered_count=triggered,
        execution_ids=execution_ids,
    )
