"""Owner-side endpoints for the hosted-app surface.

Post-refactor: no publish / unpublish / versions / rollback. The
workflow's ``is_active`` flag IS the switch. This router only owns:

- Secrets: set password, mint / rotate API key
- Analytics: sessions, cost, retention, top prompts
- Session moderation: list, block
"""

import uuid
from collections import Counter
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.features.apps.models import AppMessage, AppSession
from apps.api.app.features.apps.schemas import (
    AnalyticsOverview,
    ApiKeyOut,
    AppPasswordIn,
)
from apps.api.app.features.apps.service import AppService
from apps.api.app.features.users.models import User
from apps.api.app.features.workflows.models import Workflow
from apps.api.app.features.workflows.repository import WorkflowRepository
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.features.workspaces.service import WorkspaceService
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

router = APIRouter()


async def _get_workflow(workflow_id: uuid.UUID, workspace: Workspace, db: AsyncSession) -> Workflow:
    wf = await WorkflowRepository(db).get_by_id_and_workspace(workflow_id, workspace.id)
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return wf


@router.put("/{workflow_id}/app/password")
async def set_password(
    workflow_id: uuid.UUID,
    body: AppPasswordIn,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    wf = await _get_workflow(workflow_id, workspace, db)
    await AppService(db).set_password(wf, body.password or "")
    return {"set": bool(body.password)}


@router.post("/{workflow_id}/app/reset-api-key", response_model=ApiKeyOut)
async def reset_api_key(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    wf = await _get_workflow(workflow_id, workspace, db)
    plain = await AppService(db).rotate_api_key(wf)
    return ApiKeyOut(api_key=plain)


@router.get("/{workflow_id}/app/analytics", response_model=AnalyticsOverview)
async def analytics(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    wf = await _get_workflow(workflow_id, workspace, db)

    sessions = list(
        (await db.execute(select(AppSession).where(AppSession.workflow_id == wf.id)))
        .scalars()
        .all()
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
    top = Counter(p.strip() for p in user_prompts).most_common(10)

    costs = sorted(float(s.total_cost_usd or 0.0) for s in sessions)

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
        top_prompts=[{"prompt": p, "count": c} for p, c in top],
        session_cost_p50=_pct(costs, 0.5),
        session_cost_p95=_pct(costs, 0.95),
    )


@router.get("/{workflow_id}/app/sessions", response_model=list[dict])
async def list_sessions(
    workflow_id: uuid.UUID,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    wf = await _get_workflow(workflow_id, workspace, db)
    sessions = await AppService(db).session_repo.list_by_workflow(wf.id, limit=limit)
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
    wf = await _get_workflow(workflow_id, workspace, db)
    service = AppService(db)
    session = await service.session_repo.get_by_id(session_id)
    if not session or session.workflow_id != wf.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    await service.session_repo.update(session, {"is_blocked": True})
    return {"blocked": True}
