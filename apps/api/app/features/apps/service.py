"""Business logic for Publish-as-App.

Two audiences:
- Owner side — publish, unpublish, list versions, analytics
- Public side — resolve app config, session get-or-create, send message
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

from apps.api.app.features.apps.models import (
    AppMessage,
    AppSession,
    PublishedApp,
)
from apps.api.app.features.apps.repository import (
    AppEventRepository,
    AppMessageRepository,
    AppSessionRepository,
    PublishedAppRepository,
)
from apps.api.app.features.apps.schemas import PublishAppRequest
from apps.api.app.features.users.models import User
from apps.api.app.features.workflows.repository import WorkflowRepository
from apps.api.app.features.workspaces.models import Workspace
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


class PublishedAppService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = PublishedAppRepository(db)
        self.session_repo = AppSessionRepository(db)
        self.message_repo = AppMessageRepository(db)
        self.event_repo = AppEventRepository(db)

    # ── Owner side ────────────────────────────────────────────────

    async def publish(
        self,
        workflow_id: uuid.UUID,
        data: PublishAppRequest,
        user: User,
        workspace: Workspace,
    ) -> PublishedApp:
        """Publish (or re-publish) a workflow as an app.

        Snapshots the current graph. If an active version exists, this
        supersedes it with an incremented version_num — the prior row
        becomes inactive but stays queryable for rollback.
        """
        wf_repo = WorkflowRepository(self.db)
        workflow = await wf_repo.get_by_id_and_workspace(workflow_id, workspace.id)
        if not workflow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

        # Locate the trigger.chat_app node in the graph to inherit defaults.
        graph = workflow.graph or {"nodes": [], "edges": []}
        chat_node = _find_chat_app_node(graph)
        if chat_node is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Workflow must contain a 'Chat App' trigger node before it can be published."
                ),
            )
        node_props = (chat_node.get("data") or {}).get("properties", {}) or {}

        # Resolve slug — explicit override > trigger prop > slugified title
        slug = (
            data.app_slug
            or node_props.get("app_slug")
            or _slugify(data.title or node_props.get("title") or workflow.name)
        )
        slug = _slugify(slug)

        # Slug uniqueness across active rows in this workspace only. If a
        # prior version of this same workflow is on the slug, we're doing a
        # re-publish and the collision is expected — we deactivate below.
        collision = await self.repository.get_active_by_slug(workspace.id, slug)
        if collision and collision.workflow_id != workflow_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Slug '{slug}' is already in use by another app in this workspace.",
            )

        # Compute version_num based on prior versions of THIS workflow.
        prior = await self.repository.list_versions_for_workflow(workflow_id)
        next_version = (prior[0].version_num + 1) if prior else 1
        prior_id = prior[0].id if prior else None

        # Deactivate prior versions before inserting so the unique index
        # (workspace_id, app_slug) doesn't collide.
        await self.repository.deactivate_all_for_workflow(workflow_id)

        password_hash = None
        if data.password:
            password_hash = _ph.hash(data.password)
        elif prior:
            password_hash = prior[0].password_hash

        auth_mode = data.auth_mode or (prior[0].auth_mode if prior else "public")
        title = data.title or node_props.get("title") or workflow.name
        description = (
            data.description if data.description is not None else node_props.get("description")
        )
        mode = data.mode or node_props.get("mode") or "chat"

        # Config blob: publish-modal overrides > trigger node defaults.
        base_config = _extract_trigger_config(node_props)
        merged_config = {**base_config, **(data.config or {})}

        app = PublishedApp(
            workspace_id=workspace.id,
            workflow_id=workflow_id,
            published_by=user.id,
            app_slug=slug,
            title=title,
            description=description,
            mode=mode,
            graph_snapshot=graph,
            version_num=next_version,
            previous_version_id=prior_id,
            config=merged_config,
            auth_mode=auth_mode,
            password_hash=password_hash,
            expires_at=data.expires_at,
            is_active=True,
        )
        app = await self.repository.create(app)
        await self.event_repo.emit(app.id, "app.published", payload={"version": next_version})
        return app

    async def unpublish(self, workflow_id: uuid.UUID, user: User, workspace: Workspace) -> None:
        wf_repo = WorkflowRepository(self.db)
        workflow = await wf_repo.get_by_id_and_workspace(workflow_id, workspace.id)
        if not workflow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
        await self.repository.deactivate_all_for_workflow(workflow_id)

    async def get_for_workflow(
        self, workflow_id: uuid.UUID, workspace: Workspace
    ) -> PublishedApp | None:
        wf_repo = WorkflowRepository(self.db)
        workflow = await wf_repo.get_by_id_and_workspace(workflow_id, workspace.id)
        if not workflow:
            return None
        return await self.repository.get_active_for_workflow(workflow_id)

    async def list_versions(
        self, workflow_id: uuid.UUID, workspace: Workspace
    ) -> list[PublishedApp]:
        wf_repo = WorkflowRepository(self.db)
        workflow = await wf_repo.get_by_id_and_workspace(workflow_id, workspace.id)
        if not workflow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
        return await self.repository.list_versions_for_workflow(workflow_id)

    # ── Public side ───────────────────────────────────────────────

    async def resolve_public_app(self, workspace_slug: str, app_slug: str) -> PublishedApp:
        ws = await WorkspaceRepository(self.db).get_by_slug(workspace_slug)
        if not ws:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
        app = await self.repository.get_active_by_slug(ws.id, app_slug)
        if not app or not app.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
        if app.expires_at and app.expires_at < datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="This app has expired")
        return app

    def verify_password(self, app: PublishedApp, password: str) -> bool:
        if not app.password_hash:
            return False
        try:
            return _ph.verify(app.password_hash, password)
        except VerifyMismatchError:
            return False

    @staticmethod
    def make_api_key() -> tuple[str, str]:
        """Return (plain, hash). Plain shown to owner once at generation."""
        plain = secrets.token_urlsafe(32)
        return plain, _ph.hash(plain)

    def verify_api_key(self, app: PublishedApp, key: str) -> bool:
        if not app.api_key_hash or not key:
            return False
        try:
            return _ph.verify(app.api_key_hash, key)
        except VerifyMismatchError:
            return False

    async def rollback_to_version(
        self,
        workflow_id: uuid.UUID,
        version_num: int,
        user: User,
        workspace: Workspace,
    ) -> PublishedApp:
        """Activate a prior version by copying it forward as a new active row.

        Rather than flipping is_active on the old row (which would let a
        stale slug collide), we snapshot the historical config + graph
        into a new PublishedApp with an incremented version_num.
        """
        wf_repo = WorkflowRepository(self.db)
        workflow = await wf_repo.get_by_id_and_workspace(workflow_id, workspace.id)
        if not workflow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
        versions = await self.repository.list_versions_for_workflow(workflow_id)
        target = next((v for v in versions if v.version_num == version_num), None)
        if target is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_num} not found",
            )
        next_version = (versions[0].version_num + 1) if versions else 1
        await self.repository.deactivate_all_for_workflow(workflow_id)
        rolled = PublishedApp(
            workspace_id=workspace.id,
            workflow_id=workflow_id,
            published_by=user.id,
            app_slug=target.app_slug,
            title=target.title,
            description=target.description,
            mode=target.mode,
            graph_snapshot=target.graph_snapshot,
            version_num=next_version,
            previous_version_id=target.id,
            config=target.config,
            auth_mode=target.auth_mode,
            password_hash=target.password_hash,
            api_key_hash=target.api_key_hash,
            expires_at=target.expires_at,
            is_active=True,
        )
        rolled = await self.repository.create(rolled)
        await self.event_repo.emit(
            rolled.id,
            "app.rolled_back",
            payload={"to_version": target.version_num, "new_version": next_version},
        )
        return rolled

    async def get_or_create_session(
        self,
        app: PublishedApp,
        cookie_id: str | None,
        user_id: uuid.UUID | None,
        ip: str | None,
    ) -> AppSession:
        if cookie_id:
            existing = await self.session_repo.get_by_cookie(app.id, cookie_id)
            if existing:
                await self.session_repo.update(existing, {"last_seen_at": datetime.now(UTC)})
                return existing
        new_cookie = cookie_id or secrets.token_urlsafe(24)
        session = AppSession(
            app_id=app.id,
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

    async def finalize_assistant_message(
        self,
        message: AppMessage,
        content: str,
        artifacts: list[dict[str, Any]],
        tokens: int,
        cost_usd: float,
        latency_ms: int,
        is_error: bool = False,
    ) -> AppMessage:
        return await self.message_repo.update(
            message,
            {
                "content": content,
                "artifacts": artifacts,
                "tokens": tokens,
                "cost_usd": cost_usd,
                "latency_ms": latency_ms,
                "is_error": is_error,
            },
        )


def _find_chat_app_node(graph: dict[str, Any]) -> dict[str, Any] | None:
    for node in (graph or {}).get("nodes") or []:
        if isinstance(node, dict) and node.get("type") == "trigger.chat_app":
            return node
    return None


def _extract_trigger_config(props: dict[str, Any]) -> dict[str, Any]:
    """Pull the publishable subset of a trigger.chat_app node's properties."""
    keys = (
        "welcome_headline",
        "welcome_sub",
        "welcome_message",
        "suggested_prompts",
        "input_fields",
        "system_persona_id",
        "allow_history",
        "output_target",
    )
    return {k: props.get(k) for k in keys if k in props}
