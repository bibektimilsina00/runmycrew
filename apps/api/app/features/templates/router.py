"""HTTP surface for the template marketplace.

Mounted at `/api/v1/templates` (see `apps/api/app/api/v1/router.py`).
Every endpoint authenticates via `get_current_user`; mutating routes
also resolve `get_current_workspace` so we can stamp creator_id +
workspace_id on new rows.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

from .schemas import (
    InstallResultOut,
    PublishTemplateIn,
    TemplateCategoryListResponse,
    TemplateDetailOut,
    TemplateListOut,
    TemplateListResponse,
    UpdateTemplateIn,
)
from .service import TemplateService, get_template_service

router = APIRouter()


@router.get("/", response_model=TemplateListResponse)
async def list_marketplace(
    category: str | None = None,
    kind: str | None = None,
    q: str | None = None,
    sort: str = Query("newest", pattern="^(newest|popular|price-low|price-high)$"),
    limit: int = Query(24, ge=1, le=60),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
) -> TemplateListResponse:
    """Marketplace grid — paginated, filterable."""
    return await service.list_marketplace(
        category=category,
        kind=kind,
        q=q,
        sort=sort,  # type: ignore[arg-type]
        limit=limit,
        offset=offset,
    )


@router.get("/public", response_model=TemplateListResponse)
async def list_public(
    category: str | None = None,
    limit: int = Query(60, ge=1, le=60),
    offset: int = Query(0, ge=0),
    service: TemplateService = Depends(get_template_service),
) -> TemplateListResponse:
    """Anonymous marketing endpoint — official + published templates only.

    Used by the marketing site (runmycrew.com/templates). Skips auth so
    visitors don't need an account to browse the curated set; restricted
    to ``is_official=True`` so user-published rows never surface here
    until a moderation flow exists.
    """
    return await service.list_public(category=category, limit=limit, offset=offset)


@router.get("/categories", response_model=TemplateCategoryListResponse)
async def list_categories(
    _: User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
) -> TemplateCategoryListResponse:
    return TemplateCategoryListResponse(categories=await service.list_categories())


@router.get("/mine", response_model=list[TemplateListOut])
async def list_mine(
    current_user: User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
) -> list[TemplateListOut]:
    """Templates this user has published (drafts + live)."""
    return await service.list_mine(current_user)


@router.post("/publish", response_model=TemplateListOut, status_code=status.HTTP_201_CREATED)
async def publish_from_workflow(
    body: PublishTemplateIn,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: TemplateService = Depends(get_template_service),
) -> TemplateListOut:
    """Snapshot a workflow the caller owns into a fresh marketplace row."""
    return await service.publish_from_workflow(body, current_user, workspace)


@router.get("/{slug_or_id}", response_model=TemplateDetailOut)
async def get_detail(
    slug_or_id: str,
    _: User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
) -> TemplateDetailOut:
    return await service.get_detail(slug_or_id)


@router.put("/{template_id}", response_model=TemplateListOut)
async def update_template(
    template_id: UUID,
    body: UpdateTemplateIn,
    current_user: User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
) -> TemplateListOut:
    return await service.update_template(template_id, body, current_user)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
) -> None:
    await service.delete_template(template_id, current_user)


@router.post("/{slug_or_id}/install", response_model=InstallResultOut)
async def install_template(
    slug_or_id: str,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: TemplateService = Depends(get_template_service),
) -> InstallResultOut:
    return await service.install(slug_or_id, current_user, workspace)


@router.post("/{slug_or_id}/purchase", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def purchase_template(
    slug_or_id: str,
    _user: User = Depends(get_current_user),
    _ws: Workspace = Depends(get_current_workspace),
):
    """Stripe Checkout slot — wired in a follow-up PR.

    Returning a stable 501 lets the frontend show its "Coming soon"
    toast without ambiguity vs other error codes.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Template purchases are coming soon",
    )
