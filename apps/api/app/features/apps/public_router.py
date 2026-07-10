"""Public visitor endpoints for the hosted app page.

Namespace: ``/api/v1/apps/{workspace_slug}/{app_slug}/...``

Refactored: no ``PublishedApp`` row. Each request resolves the workflow
with a matching ``trigger.chat_app`` slug + ``is_active=True`` and serves
the current graph directly.

Visitor identity:
- Anonymous session cookie (``fuse_app_session``) — public / password apps
- Standard Fuse ``Authorization: Bearer`` — ``auth_mode=login``
- ``X-App-Key`` header — ``auth_mode=api_key``
"""

from __future__ import annotations

import base64
import hashlib
import mimetypes
import uuid
from typing import Any

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.features.apps.models import AppFile
from apps.api.app.features.apps.rate_limit import check_rate_limit
from apps.api.app.features.apps.schemas import (
    MessageIn,
    MessageOut,
    PublicAppOut,
    SendMessageOut,
    SessionEnvelope,
    SessionOut,
)
from apps.api.app.features.apps.service import AppService, hash_ip
from apps.api.app.features.apps.streaming import stream_execution_events

router = APIRouter()

SESSION_COOKIE = "fuse_app_session"
SESSION_COOKIE_MAX_AGE = 60 * 60 * 24 * 30
UNLOCK_COOKIE = "fuse_app_unlock"
UNLOCK_COOKIE_MAX_AGE = 60 * 60 * 24 * 7


class UnlockRequest(BaseModel):
    password: str


def _client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for") or request.headers.get("x-real-ip")
    if fwd:
        return fwd.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _issue_session_cookie(
    response: Response, workspace_slug: str, app_slug: str, cookie_id: str
) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=cookie_id,
        max_age=SESSION_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        path=f"/api/v1/apps/{workspace_slug}/{app_slug}",
    )


def _issue_unlock_cookie(
    response: Response, workspace_slug: str, app_slug: str, token: str
) -> None:
    response.set_cookie(
        key=UNLOCK_COOKIE,
        value=token,
        max_age=UNLOCK_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        path=f"/api/v1/apps/{workspace_slug}/{app_slug}",
    )


def _unlock_token_for(workflow_id: uuid.UUID, password_hash: str | None) -> str:
    seed = f"{workflow_id}:{password_hash or ''}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


async def _resolve_authenticated_user_id(request: Request, db: AsyncSession) -> uuid.UUID | None:
    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    try:
        from jose import jwt

        from apps.api.app.core.config import settings
        from apps.api.app.features.users.repository import UserRepository

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if not email:
            return None
        user = await UserRepository(db).get_by_email(email=email)
        return user.id if user and user.is_active else None
    except Exception:  # noqa: BLE001
        return None


async def _enforce_auth(
    workflow: Any,
    trigger_props: dict[str, Any],
    request: Request,
    unlock_cookie: str | None,
    db: AsyncSession,
) -> uuid.UUID | None:
    mode = trigger_props.get("auth_mode") or "public"
    if mode == "public":
        return None
    if mode == "password":
        expected = _unlock_token_for(workflow.id, workflow.app_password_hash)
        if unlock_cookie != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="password_required"
            )
        return None
    if mode == "login":
        user_id = await _resolve_authenticated_user_id(request, db)
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="login_required")
        return user_id
    if mode == "api_key":
        provided = request.headers.get("x-app-key")
        if not provided:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="api_key_required")
        svc = AppService.__new__(AppService)
        if not svc.verify_api_key(workflow, provided):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_api_key")
        return None
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unknown auth mode"
    )


_PUBLIC_CONFIG_KEYS = {
    "welcome_headline",
    "welcome_sub",
    "welcome_message",
    "suggested_prompts",
    "input_fields",
    "system_persona_id",
    "allow_history",
    "output_target",
    "allow_file_upload",
    "allowed_file_types",
    "max_file_size_mb",
    "primary_color",
    "logo_url",
    "dark_mode",
    "show_powered_by",
    "og_image_url",
    "rate_limit_per_min",
    "session_cost_cap_usd",
    "daily_cost_cap_usd",
}


def _public_out(
    workspace_slug: str, app_slug: str, workflow: Any, props: dict[str, Any]
) -> PublicAppOut:
    config = {k: v for k, v in props.items() if k in _PUBLIC_CONFIG_KEYS}
    return PublicAppOut(
        workflow_id=workflow.id,
        workspace_slug=workspace_slug,
        app_slug=app_slug,
        title=props.get("title") or workflow.name,
        description=props.get("description") or workflow.description,
        mode=props.get("mode") or "chat",
        auth_mode=props.get("auth_mode") or "public",
        config=config,
        public_url=f"/apps/{workspace_slug}/{app_slug}",
    )


@router.get("/{workspace_slug}/{app_slug}", response_model=PublicAppOut)
async def get_public_app(workspace_slug: str, app_slug: str, db: AsyncSession = Depends(get_db)):
    wf, props = await AppService(db).resolve_public_app(workspace_slug, app_slug)
    return _public_out(workspace_slug, app_slug, wf, props)


@router.post("/{workspace_slug}/{app_slug}/unlock")
async def unlock_password(
    workspace_slug: str,
    app_slug: str,
    body: UnlockRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    service = AppService(db)
    wf, props = await service.resolve_public_app(workspace_slug, app_slug)
    if (props.get("auth_mode") or "public") != "password":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="not_password_gated")
    ok, retry = await check_rate_limit(
        wf.id, "unlock", hash_ip(_client_ip(request)), max_per_minute=8
    )
    if not ok:
        response.headers["Retry-After"] = str(retry)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="rate_limited")
    if not service.verify_password(wf, body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_password")
    token = _unlock_token_for(wf.id, wf.app_password_hash)
    _issue_unlock_cookie(response, workspace_slug, app_slug, token)
    return {"unlocked": True}


@router.post("/{workspace_slug}/{app_slug}/session", response_model=SessionEnvelope)
async def get_or_create_session(
    workspace_slug: str,
    app_slug: str,
    request: Request,
    response: Response,
    session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    unlock_cookie: str | None = Cookie(default=None, alias=UNLOCK_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    service = AppService(db)
    wf, props = await service.resolve_public_app(workspace_slug, app_slug)
    user_id = await _enforce_auth(wf, props, request, unlock_cookie, db)
    session = await service.get_or_create_session(
        wf, cookie_id=session_cookie, user_id=user_id, ip=_client_ip(request)
    )
    _issue_session_cookie(response, workspace_slug, app_slug, session.cookie_id)
    messages = await service.list_messages(session, limit=50)
    return SessionEnvelope(
        session=SessionOut(
            id=session.id,
            workflow_id=session.workflow_id,
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


@router.post("/{workspace_slug}/{app_slug}/message", response_model=SendMessageOut)
async def send_message(
    workspace_slug: str,
    app_slug: str,
    payload: MessageIn,
    request: Request,
    response: Response,
    session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    unlock_cookie: str | None = Cookie(default=None, alias=UNLOCK_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    if session_cookie is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session cookie missing — call /session first.",
        )
    service = AppService(db)
    wf, props = await service.resolve_public_app(workspace_slug, app_slug)
    user_id = await _enforce_auth(wf, props, request, unlock_cookie, db)
    session = await service.get_or_create_session(
        wf, cookie_id=session_cookie, user_id=user_id, ip=_client_ip(request)
    )
    if session.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This session has been blocked by the app owner.",
        )
    if not payload.message and not payload.form_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Message body is required."
        )

    max_per_min = int(props.get("rate_limit_per_min") or 20)
    session_cap = float(props.get("session_cost_cap_usd") or 0.0)
    daily_cap = float(props.get("daily_cost_cap_usd") or 0.0)

    ok, retry = await check_rate_limit(
        wf.id, str(session.id), hash_ip(_client_ip(request)), max_per_minute=max_per_min
    )
    if not ok:
        response.headers["Retry-After"] = str(retry)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="rate_limited")

    if session_cap > 0 and (session.total_cost_usd or 0) >= session_cap:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="session_cost_cap_reached"
        )
    if daily_cap > 0:
        from datetime import UTC, datetime

        from sqlalchemy import select

        from apps.api.app.features.apps.models import AppSession as _S

        today = datetime.now(UTC).date()
        rows = await db.execute(select(_S).where(_S.workflow_id == wf.id))
        spent_today = 0.0
        for r in rows.scalars().all():
            if r.last_seen_at and r.last_seen_at.date() == today:
                spent_today += float(r.total_cost_usd or 0.0)
        if spent_today >= daily_cap:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="daily_cost_cap_reached",
            )

    await service.create_user_message(session, payload.message)
    execution_id = f"app-{uuid.uuid4()}"
    assistant_msg = await service.create_assistant_placeholder(session, execution_id)

    from apps.worker.app.jobs.tasks import execute_app_message

    execute_app_message.delay(
        execution_id=execution_id,
        workflow_id=str(wf.id),
        session_id=str(session.id),
        assistant_message_id=str(assistant_msg.id),
        user_message=payload.message,
        form_data=payload.form_data,
    )

    return SendMessageOut(
        message_id=assistant_msg.id,
        execution_id=execution_id,
        stream_url=f"/api/v1/apps/{workspace_slug}/{app_slug}/stream/{execution_id}",
    )


@router.get("/{workspace_slug}/{app_slug}/stream/{execution_id}")
async def stream(
    workspace_slug: str,
    app_slug: str,
    execution_id: str,
    session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    service = AppService(db)
    wf, _ = await service.resolve_public_app(workspace_slug, app_slug)
    if session_cookie is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No session")
    session = await service.session_repo.get_by_cookie(wf.id, session_cookie)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No session")
    return StreamingResponse(
        stream_execution_events(execution_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/{workspace_slug}/{app_slug}/history", response_model=list[MessageOut])
async def history(
    workspace_slug: str,
    app_slug: str,
    session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    service = AppService(db)
    wf, _ = await service.resolve_public_app(workspace_slug, app_slug)
    if session_cookie is None:
        return []
    session = await service.session_repo.get_by_cookie(wf.id, session_cookie)
    if not session:
        return []
    messages = await service.list_messages(session, limit=200)
    return [_msg_out(m) for m in messages]


@router.post("/{workspace_slug}/{app_slug}/upload")
async def upload_file(
    workspace_slug: str,
    app_slug: str,
    request: Request,
    file: UploadFile = File(...),
    session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    unlock_cookie: str | None = Cookie(default=None, alias=UNLOCK_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    if session_cookie is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No session")
    service = AppService(db)
    wf, props = await service.resolve_public_app(workspace_slug, app_slug)
    await _enforce_auth(wf, props, request, unlock_cookie, db)
    session = await service.session_repo.get_by_cookie(wf.id, session_cookie)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No session")

    if not props.get("allow_file_upload"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="file_upload_disabled")
    allowed_mimes: list[str] = list(props.get("allowed_file_types") or [])
    max_size_mb = int(props.get("max_file_size_mb") or 10)

    data = await file.read()
    if len(data) > max_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="file_too_large"
        )
    mime = (
        file.content_type
        or mimetypes.guess_type(file.filename or "")[0]
        or "application/octet-stream"
    )
    if allowed_mimes and mime not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="mime_not_allowed"
        )
    sha = hashlib.sha256(data).hexdigest()
    b64 = base64.b64encode(data).decode("ascii")
    url = f"data:{mime};base64,{b64}"

    row = AppFile(
        session_id=session.id,
        url=url,
        filename=file.filename or "upload",
        mime=mime,
        size_bytes=len(data),
        sha256=sha,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {
        "id": str(row.id),
        "url": row.url,
        "filename": row.filename,
        "mime": row.mime,
        "size_bytes": row.size_bytes,
    }


def _msg_out(m: Any) -> MessageOut:
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
