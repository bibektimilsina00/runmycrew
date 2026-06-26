"""Single endpoint serving every manifest-built webhook trigger.

Adding a webhook integration is one manifest file — the URL is fixed:

    POST /api/v1/webhooks/{provider}/{workflow_id}/{node_id}

The path carries everything the service needs to route: `provider`
resolves the manifest, `workflow_id` locates the graph,
`node_id` picks the right trigger node when a workflow has multiple
webhooks attached.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.features.webhooks.service import WebhookService

router = APIRouter()


@router.post("/webhooks/{provider}/{workflow_id}/{node_id}", tags=["webhooks"])
async def receive_webhook(
    provider: str,
    workflow_id: str,
    node_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    raw_body = await request.body()
    service = WebhookService(db)
    return await service.dispatch(
        provider=provider,
        workflow_id=workflow_id,
        node_id=node_id,
        raw_body=raw_body,
        headers=dict(request.headers),
    )
