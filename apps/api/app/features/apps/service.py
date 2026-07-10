"""Business logic for hosted apps.

Post-refactor: no ``PublishedApp`` row. The workflow IS the app.
``trigger.chat_app`` node props hold the config; ``Workflow.is_active``
is the live/off switch; ``Workflow.app_password_hash`` +
``Workflow.app_api_key_hash`` hold visitor-auth secrets outside the
graph JSON.
"""

import hashlib
import re
import secrets
import uuid
from datetime import UTC, datetime
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.features.apps.models import AppMessage, AppSession
from apps.api.app.features.apps.repository import (
    AppMessageRepository,
    AppSessionRepository,
    find_active_chat_app_workflow,
)
from apps.api.app.features.workflows.models import Workflow
from apps.api.app.features.workspaces.repository import WorkspaceRepository

_ph = PasswordHasher()

_SLUG_RE = re.compile(r"[^a-z0-9-]+")


def _slugify(text: str) -> str:
    slug = _SLUG_RE.sub("-", (text or "").lower()).strip("-")
    return slug or f"app-{uuid.uuid4().hex[:8]}"


def hash_ip(ip: str | None) -> str | None:
    if not ip:
        return None
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()


class AppService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_repo = AppSessionRepository(db)
        self.message_repo = AppMessageRepository(db)

    # ── Resolution ────────────────────────────────────────────────

    async def resolve_public_app(
        self, workspace_slug: str, app_slug: str
    ) -> tuple[Workflow, dict[str, Any]]:
        """Return (workflow, trigger_props) for a live app URL.

        Raises 404 when either the workspace, the workflow, or the
        trigger.chat_app node with a matching slug is missing / inactive.
        """
        ws = await WorkspaceRepository(self.db).get_by_slug(workspace_slug)
        if not ws:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
        hit = await find_active_chat_app_workflow(self.db, ws.id, app_slug)
        if hit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
        return hit

    # ── Auth secrets ──────────────────────────────────────────────

    def verify_password(self, workflow: Workflow, password: str) -> bool:
        if not workflow.app_password_hash:
            return False
        try:
            return _ph.verify(workflow.app_password_hash, password)
        except VerifyMismatchError:
            return False

    @staticmethod
    def make_api_key() -> tuple[str, str]:
        plain = secrets.token_urlsafe(32)
        return plain, _ph.hash(plain)

    def verify_api_key(self, workflow: Workflow, key: str) -> bool:
        if not workflow.app_api_key_hash or not key:
            return False
        try:
            return _ph.verify(workflow.app_api_key_hash, key)
        except VerifyMismatchError:
            return False

    async def set_password(self, workflow: Workflow, password: str) -> None:
        workflow.app_password_hash = _ph.hash(password) if password else None
        await self.db.commit()

    async def rotate_api_key(self, workflow: Workflow) -> str:
        plain, hashed = self.make_api_key()
        workflow.app_api_key_hash = hashed
        await self.db.commit()
        return plain

    # ── Sessions ──────────────────────────────────────────────────

    async def get_or_create_session(
        self,
        workflow: Workflow,
        cookie_id: str | None,
        user_id: uuid.UUID | None,
        ip: str | None,
    ) -> AppSession:
        if cookie_id:
            existing = await self.session_repo.get_by_cookie(workflow.id, cookie_id)
            if existing:
                await self.session_repo.update(existing, {"last_seen_at": datetime.now(UTC)})
                return existing
        new_cookie = cookie_id or secrets.token_urlsafe(24)
        session = AppSession(
            workflow_id=workflow.id,
            cookie_id=new_cookie,
            user_id=user_id,
            ip_hash=hash_ip(ip),
        )
        return await self.session_repo.create(session)

    async def list_messages(self, session: AppSession, limit: int = 100) -> list[AppMessage]:
        return await self.message_repo.list_by_session(session.id, limit=limit)

    async def create_user_message(self, session: AppSession, content: str) -> AppMessage:
        msg = AppMessage(
            session_id=session.id,
            role="user",
            content=content,
            artifacts=[],
        )
        return await self.message_repo.create(msg)

    async def create_assistant_placeholder(
        self, session: AppSession, execution_id: str
    ) -> AppMessage:
        msg = AppMessage(
            session_id=session.id,
            role="assistant",
            content="",
            artifacts=[],
            execution_id=execution_id,
        )
        return await self.message_repo.create(msg)
