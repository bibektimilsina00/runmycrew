from __future__ import annotations

from pydantic import BaseModel


class MetaResource(BaseModel):
    """A single resource attached to a Meta credential — a Page, an Instagram
    business account, a WhatsApp phone number, or a Lead Ads form."""

    id: str
    name: str
    kind: str  # 'page' | 'ig_account' | 'waba_phone' | 'lead_form'
    secondary: str | None = None  # e.g. the linked Page name, IG username, etc.


class MetaResourcesResponse(BaseModel):
    credential_id: str
    kind: str
    resources: list[MetaResource]


class MetaWebhookReceiveResponse(BaseModel):
    status: str
    triggered_count: int
    execution_ids: list[str] = []
