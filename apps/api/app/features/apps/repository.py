import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.features.apps.models import (
    AppEvent,
    AppMessage,
    AppSession,
    PublishedApp,
)


class PublishedAppRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_by_slug(
        self, workspace_id: uuid.UUID, app_slug: str
    ) -> PublishedApp | None:
        result = await self.db.execute(
            select(PublishedApp).where(
                PublishedApp.workspace_id == workspace_id,
                PublishedApp.app_slug == app_slug,
                PublishedApp.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_active_for_workflow(self, workflow_id: uuid.UUID) -> PublishedApp | None:
        result = await self.db.execute(
            select(PublishedApp).where(
                PublishedApp.workflow_id == workflow_id,
                PublishedApp.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, app_id: uuid.UUID) -> PublishedApp | None:
        result = await self.db.execute(select(PublishedApp).where(PublishedApp.id == app_id))
        return result.scalar_one_or_none()

    async def list_versions_for_workflow(self, workflow_id: uuid.UUID) -> list[PublishedApp]:
        result = await self.db.execute(
            select(PublishedApp)
            .where(PublishedApp.workflow_id == workflow_id)
            .order_by(PublishedApp.version_num.desc())
        )
        return list(result.scalars().all())

    async def create(self, app: PublishedApp) -> PublishedApp:
        self.db.add(app)
        await self.db.commit()
        await self.db.refresh(app)
        return app

    async def update(self, app: PublishedApp, data: dict) -> PublishedApp:
        for k, v in data.items():
            setattr(app, k, v)
        await self.db.commit()
        await self.db.refresh(app)
        return app

    async def deactivate_all_for_workflow(self, workflow_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(PublishedApp).where(
                PublishedApp.workflow_id == workflow_id,
                PublishedApp.is_active.is_(True),
            )
        )
        for row in result.scalars().all():
            row.is_active = False
        await self.db.commit()


class AppSessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_cookie(self, app_id: uuid.UUID, cookie_id: str) -> AppSession | None:
        result = await self.db.execute(
            select(AppSession).where(AppSession.app_id == app_id, AppSession.cookie_id == cookie_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, session_id: uuid.UUID) -> AppSession | None:
        result = await self.db.execute(select(AppSession).where(AppSession.id == session_id))
        return result.scalar_one_or_none()

    async def list_by_app(self, app_id: uuid.UUID, limit: int = 100) -> list[AppSession]:
        result = await self.db.execute(
            select(AppSession)
            .where(AppSession.app_id == app_id)
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


class AppEventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def emit(
        self,
        app_id: uuid.UUID,
        type_: str,
        session_id: uuid.UUID | None = None,
        payload: dict | None = None,
    ) -> AppEvent:
        row = AppEvent(
            app_id=app_id,
            type=type_,
            session_id=session_id,
            payload=payload or {},
        )
        self.db.add(row)
        await self.db.commit()
        return row
