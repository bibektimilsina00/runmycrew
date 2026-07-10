import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.features.apps.models import AppMessage, AppSession
from apps.api.app.features.workflows.models import Workflow


class AppSessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_cookie(self, workflow_id: uuid.UUID, cookie_id: str) -> AppSession | None:
        result = await self.db.execute(
            select(AppSession).where(
                AppSession.workflow_id == workflow_id,
                AppSession.cookie_id == cookie_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, session_id: uuid.UUID) -> AppSession | None:
        result = await self.db.execute(select(AppSession).where(AppSession.id == session_id))
        return result.scalar_one_or_none()

    async def list_by_workflow(self, workflow_id: uuid.UUID, limit: int = 100) -> list[AppSession]:
        result = await self.db.execute(
            select(AppSession)
            .where(AppSession.workflow_id == workflow_id)
            .order_by(AppSession.last_seen_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, session: AppSession) -> AppSession:
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def update(self, session: AppSession, data: dict) -> AppSession:
        for k, v in data.items():
            setattr(session, k, v)
        await self.db.commit()
        await self.db.refresh(session)
        return session


class AppMessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_session(self, session_id: uuid.UUID, limit: int = 100) -> list[AppMessage]:
        result = await self.db.execute(
            select(AppMessage)
            .where(AppMessage.session_id == session_id)
            .order_by(AppMessage.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, message_id: uuid.UUID) -> AppMessage | None:
        result = await self.db.execute(select(AppMessage).where(AppMessage.id == message_id))
        return result.scalar_one_or_none()

    async def get_by_execution(self, execution_id: str) -> AppMessage | None:
        result = await self.db.execute(
            select(AppMessage).where(AppMessage.execution_id == execution_id)
        )
        return result.scalar_one_or_none()

    async def create(self, message: AppMessage) -> AppMessage:
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def update(self, message: AppMessage, data: dict) -> AppMessage:
        for k, v in data.items():
            setattr(message, k, v)
        await self.db.commit()
        await self.db.refresh(message)
        return message


async def find_active_chat_app_workflow(
    db: AsyncSession, workspace_id: uuid.UUID, app_slug: str
) -> tuple[Workflow, dict] | None:
    """Locate the live workflow matching /apps/{workspace}/{app_slug}.

    Returns the Workflow row + the trigger.chat_app node's `data.properties`
    dict for config lookup. Filters to ``is_active=True`` workflows and to
    those whose graph contains a ``trigger.chat_app`` node with the given
    slug.
    """
    result = await db.execute(
        select(Workflow).where(
            Workflow.workspace_id == workspace_id,
            Workflow.is_active.is_(True),
        )
    )
    for wf in result.scalars().all():
        graph = wf.graph or {}
        for node in graph.get("nodes") or []:
            if not isinstance(node, dict) or node.get("type") != "trigger.chat_app":
                continue
            props = (node.get("data") or {}).get("properties") or {}
            slug = _slugify(props.get("app_slug") or props.get("title") or wf.name)
            if slug == app_slug:
                return wf, props
    return None


_SLUG_RE = re.compile(r"[^a-z0-9-]+")


def _slugify(text: str) -> str:
    slug = _SLUG_RE.sub("-", (text or "").lower()).strip("-")
    return slug or "app"
