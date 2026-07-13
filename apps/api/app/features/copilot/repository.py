import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.features.copilot.models import CopilotSession


class CopilotSessionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_target_and_user(
        self,
        *,
        workflow_id: uuid.UUID | None = None,
        crew_id: uuid.UUID | None = None,
        user_id: uuid.UUID,
        limit: int = 50,
    ) -> list[CopilotSession]:
        """Sessions for a workflow OR crew (exactly one id set)."""
        target = (
            CopilotSession.workflow_id == workflow_id
            if workflow_id is not None
            else CopilotSession.crew_id == crew_id
        )
        result = await self.db.execute(
            select(CopilotSession)
            .where(target, CopilotSession.user_id == user_id)
            .order_by(CopilotSession.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id_and_user(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> CopilotSession | None:
        result = await self.db.execute(
            select(CopilotSession).where(
                CopilotSession.id == session_id,
                CopilotSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, session: CopilotSession) -> CopilotSession:
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def update(self, session: CopilotSession, data: dict) -> CopilotSession:
        for key, value in data.items():
            setattr(session, key, value)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def delete(self, session: CopilotSession) -> None:
        await self.db.delete(session)
        await self.db.commit()
