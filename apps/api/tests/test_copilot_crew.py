"""Copilot resolves crew ids as well as workflow ids, and persists a
session against the right owner column. This is what lets the dashboard
'build a crew with AI' flow work — copilot builds crews with the same
graph tools it uses for workflows."""

import uuid

import pytest
from sqlalchemy import delete, text

import apps.api.app.main  # noqa: F401 — registers ORM models
from apps.api.app.core.database import AsyncSessionLocal
from apps.api.app.features.copilot.models import CopilotSession
from apps.api.app.features.copilot.repository import CopilotSessionRepository
from apps.api.app.features.copilot.service import CopilotService
from apps.api.app.features.crews.models import Crew
from apps.api.app.features.users.models import User
from apps.api.app.features.workflows.models import Workflow
from apps.api.app.features.workspaces.models import Workspace


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def _db_available() -> bool:
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def _seed():
    suffix = uuid.uuid4().hex[:8]
    async with AsyncSessionLocal() as db:
        user = User(email=f"cop-{suffix}@t.com", hashed_password="x", is_active=True)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        ws = Workspace(slug=f"cop-{suffix}", owner_id=user.id, name="W")
        db.add(ws)
        await db.commit()
        await db.refresh(ws)
        wf = Workflow(
            name="WF", user_id=user.id, workspace_id=ws.id, graph={"nodes": [], "edges": []}
        )
        crew = Crew(
            name="CR", user_id=user.id, workspace_id=ws.id, graph={"nodes": [], "edges": []}
        )
        db.add(wf)
        db.add(crew)
        await db.commit()
        await db.refresh(wf)
        await db.refresh(crew)
        return user, wf, crew


async def _cleanup(user_id):
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Workspace).where(Workspace.owner_id == user_id))
        await db.execute(delete(Workflow).where(Workflow.user_id == user_id))
        await db.execute(delete(Crew).where(Crew.user_id == user_id))
        await db.execute(delete(User).where(User.id == user_id))
        await db.commit()


@pytest.mark.anyio
async def test_resolve_target_workflow_and_crew():
    if not await _db_available():
        pytest.skip("Postgres unavailable")
    user, wf, crew = await _seed()
    try:
        async with AsyncSessionLocal() as db:
            svc = CopilotService(db)
            ent_w, kind_w = await svc.resolve_target(str(wf.id), user)
            ent_c, kind_c = await svc.resolve_target(str(crew.id), user)
        assert kind_w == "workflow" and ent_w.id == wf.id
        assert kind_c == "crew" and ent_c.id == crew.id
    finally:
        await _cleanup(user.id)


@pytest.mark.anyio
async def test_resolve_target_rejects_foreign_and_unknown():
    if not await _db_available():
        pytest.skip("Postgres unavailable")
    user, wf, crew = await _seed()
    other, _, _ = await _seed()
    try:
        from fastapi import HTTPException

        async with AsyncSessionLocal() as db:
            svc = CopilotService(db)
            # Another user's crew → 404.
            with pytest.raises(HTTPException) as ei:
                await svc.resolve_target(str(crew.id), other)
            assert ei.value.status_code == 404
            # Nonexistent id → 404.
            with pytest.raises(HTTPException):
                await svc.resolve_target(str(uuid.uuid4()), user)
    finally:
        await _cleanup(user.id)
        await _cleanup(other.id)


@pytest.mark.anyio
async def test_copilot_session_persists_with_crew_id():
    """A session created for a crew hangs off crew_id, and list_sessions for
    that crew returns it (and not the workflow's)."""
    if not await _db_available():
        pytest.skip("Postgres unavailable")
    user, wf, crew = await _seed()
    try:
        async with AsyncSessionLocal() as db:
            repo = CopilotSessionRepository(db)
            await repo.create(
                CopilotSession(crew_id=crew.id, user_id=user.id, title="crew chat", messages=[])
            )
            await repo.create(
                CopilotSession(workflow_id=wf.id, user_id=user.id, title="wf chat", messages=[])
            )
            crew_sessions = await repo.list_by_target_and_user(crew_id=crew.id, user_id=user.id)
            wf_sessions = await repo.list_by_target_and_user(workflow_id=wf.id, user_id=user.id)
        assert [s.title for s in crew_sessions] == ["crew chat"]
        assert [s.title for s in wf_sessions] == ["wf chat"]
    finally:
        await _cleanup(user.id)
