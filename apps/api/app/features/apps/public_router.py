"""Public visitor endpoints for the hosted app page.

Namespace: ``/api/v1/apps/{workspace_slug}/{app_slug}/...``

No JWT — visitor identity is either the anonymous session cookie
(``fuse_app_session``) or, when the app requires login, the standard
Fuse ``Authorization: Bearer <token>`` header.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.features.apps.schemas import (
    MessageIn,
    MessageOut,
    PublicAppOut,
    SendMessageOut,
    SessionEnvelope,
    SessionOut,
)
from apps.api.app.features.apps.service import PublishedAppService
from apps.api.app.features.apps.streaming import stream_execution_events

router = APIRouter()

SESSION_COOKIE = "fuse_app_session"
SESSION_COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def _client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for") or request.headers.get("x-real-ip")
    if fwd:
        return fwd.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


@router.get(
    "/{workspace_slug}/{app_slug}",
    response_model=PublicAppOut,
)
async def get_public_app(
    workspace_slug: str,
    app_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Public config used to render the chat page.

    Excludes ``graph_snapshot``, ``password_hash``, ``api_key_hash``. Safe
    to expose to unauthenticated visitors.
    """
    app = await PublishedAppService(db).resolve_public_app(workspace_slug, app_slug)
    return PublicAppOut(
        id=app.id,
        app_slug=app.app_slug,
        title=app.title,
        description=app.description,
        mode=app.mode,
        version_num=app.version_num,
        config=app.config or {},
        auth_mode=app.auth_mode,
        published_at=app.published_at,
        expires_at=app.expires_at,
    )


@router.post(
    "/{workspace_slug}/{app_slug}/session",
    response_model=SessionEnvelope,
)
async def get_or_create_session(
    workspace_slug: str,
    app_slug: str,
    request: Request,
    response: Response,
    session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    """Get-or-create the visitor's session and return the recent message history.

    Sets the session cookie (30-day, HttpOnly, SameSite=Lax) on first hit so
    subsequent turns route to the same thread.
    """
    service = PublishedAppService(db)
    app = await service.resolve_public_app(workspace_slug, app_slug)
    if app.auth_mode == "public":
        pass
    elif app.auth_mode == "password":
        # Password mode uses a separate token exchange — clients POST
        # /session with valid credentials via a pre-check we'll wire in
        # PR-C. For PR-A only ``public`` is exercised.
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Password-gated apps ship in PR-C",
        )
    elif app.auth_mode in ("login", "api_key"):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"'{app.auth_mode}' auth ships in PR-C",
        )
    session = await service.get_or_create_session(
        app,
        cookie_id=session_cookie,
        user_id=None,
        ip=_client_ip(request),
    )
    # (Re-)issue the cookie so it renews the TTL on every visit.
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session.cookie_id,
        max_age=SESSION_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        path=f"/api/v1/apps/{workspace_slug}/{app_slug}",
    )
    messages = await service.list_messages(session, limit=50)
    return SessionEnvelope(
        session=SessionOut(
            id=session.id,
            app_id=session.app_id,
            cookie_id=session.cookie_id,
            user_id=session.user_id,
            first_seen_at=session.first_seen_at,
            last_seen_at=session.last_seen_at,
            message_count=session.message_count,
            total_cost_usd=session.total_cost_usd,
            total_tokens=session.total_tokens,
            is_blocked=session.is_blocked,
        ),
        messages=[_msg_out(m) for m in messages],
    )


@router.post(
    "/{workspace_slug}/{app_slug}/message",
    response_model=SendMessageOut,
)
async def send_message(
    workspace_slug: str,
    app_slug: str,
    payload: MessageIn,
    request: Request,
    session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    """Enqueue a workflow execution for this turn.

    Creates a user AppMessage + an assistant placeholder, then hands the
    graph snapshot + turn payload to the Celery worker. Returns the ids
    the SSE endpoint uses to stream progress.
    """
    if session_cookie is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session cookie missing — call /session first.",
        )
    service = PublishedAppService(db)
    app = await service.resolve_public_app(workspace_slug, app_slug)
    session = await service.get_or_create_session(
        app,
        cookie_id=session_cookie,
        user_id=None,
        ip=_client_ip(request),
    )
    if session.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This session has been blocked by the app owner.",
        )
    if not payload.message and not payload.form_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message body is required.",
        )
    # Persist the user turn immediately so history is queryable while
    # the assistant response is still streaming.
    await service.create_user_message(session, payload.message)
    execution_id = f"app-{uuid.uuid4()}"
    assistant_msg = await service.create_assistant_placeholder(session, execution_id)

    # Enqueue the run
    from apps.worker.app.jobs.tasks import execute_app_message

    execute_app_message.delay(
        execution_id=execution_id,
        published_app_id=str(app.id),
        session_id=str(session.id),
        assistant_message_id=str(assistant_msg.id),
        user_message=payload.message,
        form_data=payload.form_data,
    )

    return SendMessageOut(
        message_id=assistant_msg.id,
        execution_id=execution_id,
        stream_url=(f"/api/v1/apps/{workspace_slug}/{app_slug}/stream/{execution_id}"),
    )


@router.get("/{workspace_slug}/{app_slug}/stream/{execution_id}")
async def stream(
    workspace_slug: str,
    app_slug: str,
    execution_id: str,
    session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    """SSE — forwards workflow-runner events to the client.

    Contract: `event: <type>\\ndata: <json>\\n\\n`. Terminal event
    `stream_end` signals the client to close.
    """
    service = PublishedAppService(db)
    app = await service.resolve_public_app(workspace_slug, app_slug)
    if session_cookie is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No session")
    session = await service.session_repo.get_by_cookie(app.id, session_cookie)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No session")

    return StreamingResponse(
        stream_execution_events(execution_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",  # nginx: disable proxy buffering
            "Connection": "keep-alive",
        },
    )


@router.get(
    "/{workspace_slug}/{app_slug}/history",
    response_model=list[MessageOut],
)
async def history(
    workspace_slug: str,
    app_slug: str,
    session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    service = PublishedAppService(db)
    app = await service.resolve_public_app(workspace_slug, app_slug)
    if session_cookie is None:
        return []
    session = await service.session_repo.get_by_cookie(app.id, session_cookie)
    if not session:
        return []
    messages = await service.list_messages(session, limit=200)
    return [_msg_out(m) for m in messages]


def _msg_out(m) -> MessageOut:
    return MessageOut(
        id=m.id,
        session_id=m.session_id,
        role=m.role,
        content=m.content,
        artifacts=m.artifacts or [],
        execution_id=m.execution_id,
        tokens=m.tokens,
        cost_usd=m.cost_usd,
        latency_ms=m.latency_ms,
        is_error=m.is_error,
        created_at=m.created_at,
    )
