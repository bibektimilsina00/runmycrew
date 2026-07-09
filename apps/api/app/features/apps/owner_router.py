"""Owner-side endpoints: publish, unpublish, list versions, analytics.

Mounted under the /workflows router — all endpoints route through
``/workflows/{workflow_id}/app...`` so app management lives alongside the
workflow it belongs to.
"""

import uuid
from collections import Counter
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.config import settings
from apps.api.app.core.database import get_db
from apps.api.app.features.apps.models import AppMessage, AppSession
from apps.api.app.features.apps.schemas import (
    AnalyticsOverview,
    ApiKeyOut,
    PublishAppRequest,
    PublishedAppOut,
    RollbackRequest,
)
from apps.api.app.features.apps.service import PublishedAppService
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.features.workspaces.service import WorkspaceService
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

router = APIRouter()


def _to_public_url(workspace_slug: str, app_slug: str) -> str:
    base = getattr(settings, "PUBLIC_APP_BASE_URL", None) or ""
    base = base.rstrip("/")
    return (
        f"{base}/apps/{workspace_slug}/{app_slug}" if base else f"/apps/{workspace_slug}/{app_slug}"
    )


@router.post(
    "/{workflow_id}/publish",
    response_model=PublishedAppOut,
    status_code=status.HTTP_201_CREATED,
)
async def publish_workflow(
    workflow_id: uuid.UUID,
    data: PublishAppRequest,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Publish (or re-publish) the workflow at this ID as a hosted app."""
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    service = PublishedAppService(db)
    app = await service.publish(workflow_id, data, current_user, workspace)
    return _wrap(app, workspace.slug)


@router.delete(
    "/{workflow_id}/publish",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def unpublish_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    await PublishedAppService(db).unpublish(workflow_id, current_user, workspace)


@router.get("/{workflow_id}/app", response_model=PublishedAppOut | None)
async def get_current_app(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    app = await PublishedAppService(db).get_for_workflow(workflow_id, workspace)
    return _wrap(app, workspace.slug) if app else None


@router.get("/{workflow_id}/app/versions", response_model=list[PublishedAppOut])
async def list_versions(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    versions = await PublishedAppService(db).list_versions(workflow_id, workspace)
    return [_wrap(v, workspace.slug) for v in versions]


@router.post(
    "/{workflow_id}/app/rollback",
    response_model=PublishedAppOut,
    status_code=status.HTTP_201_CREATED,
)
async def rollback(
    workflow_id: uuid.UUID,
    data: RollbackRequest,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Promote a prior published version back to active by copying it forward."""
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    app = await PublishedAppService(db).rollback_to_version(
        workflow_id, data.version_num, current_user, workspace
    )
    return _wrap(app, workspace.slug)


@router.post(
    "/{workflow_id}/app/reset-api-key",
    response_model=ApiKeyOut,
)
async def reset_api_key(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Mint a fresh API key for the active app and stash its hash.

    Plain key returned ONCE — owner must save it. Rotating the key
    invalidates every prior key immediately.
    """
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    service = PublishedAppService(db)
    app = await service.get_for_workflow(workflow_id, workspace)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active app")
    plain, hashed = PublishedAppService.make_api_key()
    await service.repository.update(app, {"api_key_hash": hashed})
    return ApiKeyOut(api_key=plain)


@router.get(
    "/{workflow_id}/app/analytics",
    response_model=AnalyticsOverview,
)
async def analytics(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Owner analytics: totals, today, retention proxy, top prompts."""
    service = PublishedAppService(db)
    app = await service.get_for_workflow(workflow_id, workspace)
    if not app:
        return AnalyticsOverview(
            total_sessions=0,
            total_messages=0,
            total_cost_usd=0.0,
            active_today=0,
            messages_today=0,
            cost_today=0.0,
            top_prompts=[],
            session_cost_p50=0.0,
            session_cost_p95=0.0,
        )

    sessions = list(
        (await db.execute(select(AppSession).where(AppSession.app_id == app.id))).scalars().all()
    )
    session_ids = [s.id for s in sessions]
    messages: list[AppMessage] = []
    if session_ids:
        messages = list(
            (await db.execute(select(AppMessage).where(AppMessage.session_id.in_(session_ids))))
            .scalars()
            .all()
        )

    today = datetime.now(UTC).date()
    active_today = sum(1 for s in sessions if s.last_seen_at and s.last_seen_at.date() == today)
    msgs_today = [m for m in messages if m.created_at and m.created_at.date() == today]
    cost_today = sum(float(m.cost_usd or 0.0) for m in msgs_today)
    total_cost = sum(float(m.cost_usd or 0.0) for m in messages)

    user_prompts = [m.content for m in messages if m.role == "user" and (m.content or "").strip()]
    prompt_counts = Counter(p.strip() for p in user_prompts)
    top_prompts = [{"prompt": p, "count": c} for p, c in prompt_counts.most_common(10)]

    session_costs = sorted(float(s.total_cost_usd or 0.0) for s in sessions)

    def _pct(values: list[float], q: float) -> float:
        if not values:
            return 0.0
        idx = min(len(values) - 1, max(0, int(len(values) * q)))
        return values[idx]

    return AnalyticsOverview(
        total_sessions=len(sessions),
        total_messages=len(messages),
        total_cost_usd=total_cost,
        active_today=active_today,
        messages_today=len(msgs_today),
        cost_today=cost_today,
        top_prompts=top_prompts,
        session_cost_p50=_pct(session_costs, 0.5),
        session_cost_p95=_pct(session_costs, 0.95),
    )


@router.get("/{workflow_id}/app/sessions", response_model=list[dict])
async def list_sessions(
    workflow_id: uuid.UUID,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    service = PublishedAppService(db)
    app = await service.get_for_workflow(workflow_id, workspace)
    if not app:
        return []
    sessions = await service.session_repo.list_by_app(app.id, limit=limit)
    return [
        {
            "id": str(s.id),
            "cookie_id": s.cookie_id,
            "first_seen_at": s.first_seen_at.isoformat() if s.first_seen_at else None,
            "last_seen_at": s.last_seen_at.isoformat() if s.last_seen_at else None,
            "message_count": s.message_count,
            "total_cost_usd": float(s.total_cost_usd or 0.0),
            "total_tokens": s.total_tokens,
            "is_blocked": s.is_blocked,
        }
        for s in sessions
    ]


@router.post("/{workflow_id}/app/sessions/{session_id}/block")
async def block_session(
    workflow_id: uuid.UUID,
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    service = PublishedAppService(db)
    app = await service.get_for_workflow(workflow_id, workspace)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active app")
    session = await service.session_repo.get_by_id(session_id)
    if not session or session.app_id != app.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    await service.session_repo.update(session, {"is_blocked": True})
    return {"blocked": True}


def _wrap(app, workspace_slug: str) -> PublishedAppOut:
    return PublishedAppOut(
        id=app.id,
        workspace_id=app.workspace_id,
        workflow_id=app.workflow_id,
        published_by=app.published_by,
        app_slug=app.app_slug,
        title=app.title,
        description=app.description,
        mode=app.mode,
        version_num=app.version_num,
        config=app.config or {},
        auth_mode=app.auth_mode,
        is_active=app.is_active,
        published_at=app.published_at,
        updated_at=app.updated_at,
        expires_at=app.expires_at,
        public_url=_to_public_url(workspace_slug, app.app_slug),
    )
