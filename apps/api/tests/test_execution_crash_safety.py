"""Executions never get stuck `running`.

Two backstops beyond the runner's own error handling:
- ``mark_terminal_if_not`` — the worker's outer crash-net, for a failure
  that escapes ``_run_workflow`` (setup crash before the inner try).
- ``reap_stale_running`` — the beat reaper, for a SIGKILL'd worker that
  runs no Python ``except`` at all.
Both are idempotent and must never clobber a run that actually finished.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete, text

import apps.api.app.main  # noqa: F401 — registers ORM models
from apps.api.app.core.database import AsyncSessionLocal
from apps.api.app.features.executions.models import Execution
from apps.api.app.features.executions.repository import ExecutionRepository
from apps.api.app.features.users.models import User
from apps.api.app.features.workflows.models import Workflow
from apps.api.app.features.workspaces.models import Workspace


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def _seed_workflow() -> tuple[uuid.UUID, uuid.UUID]:
    """Return (workflow_id, user_id) — Execution.workflow_id is a real FK."""
    suffix = uuid.uuid4().hex[:8]
    async with AsyncSessionLocal() as db:
        user = User(email=f"crash-{suffix}@fusetest.com", hashed_password="x", is_active=True)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        ws = Workspace(slug=f"crash-ws-{suffix}", owner_id=user.id, name="Crash WS")
        db.add(ws)
        await db.commit()
        await db.refresh(ws)
        wf = Workflow(
            name="Crash WF", user_id=user.id, workspace_id=ws.id, graph={"nodes": [], "edges": []}
        )
        db.add(wf)
        await db.commit()
        await db.refresh(wf)
        return wf.id, user.id


async def _drop_user(user_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Workspace).where(Workspace.owner_id == user_id))
        await db.execute(delete(Workflow).where(Workflow.user_id == user_id))
        await db.execute(delete(User).where(User.id == user_id))
        await db.commit()


async def _db_available() -> bool:
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def _make_execution(
    workflow_id: uuid.UUID, status: str, started_at: datetime | None
) -> uuid.UUID:
    async with AsyncSessionLocal() as db:
        ex = Execution(
            workflow_id=workflow_id,
            status=status,
            started_at=started_at,
            trigger_type="manual",
        )
        db.add(ex)
        await db.commit()
        await db.refresh(ex)
        return ex.id


async def _status(execution_id: uuid.UUID) -> str:
    async with AsyncSessionLocal() as db:
        repo = ExecutionRepository(db)
        ex = await repo.get_by_id(execution_id)
        return ex.status


async def _cleanup(execution_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Execution).where(Execution.id == execution_id))
        await db.commit()


@pytest.mark.anyio
async def test_mark_terminal_if_not_fails_a_running_execution():
    if not await _db_available():
        pytest.skip("Postgres unavailable")
    wf_id, user_id = await _seed_workflow()
    ex_id = await _make_execution(wf_id, "running", datetime.now(UTC))
    try:
        async with AsyncSessionLocal() as db:
            applied = await ExecutionRepository(db).mark_terminal_if_not(ex_id, "failed")
        assert applied is True
        assert await _status(ex_id) == "failed"
    finally:
        await _cleanup(ex_id)
        await _drop_user(user_id)


@pytest.mark.anyio
async def test_mark_terminal_if_not_never_clobbers_a_finished_run():
    if not await _db_available():
        pytest.skip("Postgres unavailable")
    wf_id, user_id = await _seed_workflow()
    ex_id = await _make_execution(wf_id, "completed", datetime.now(UTC))
    try:
        async with AsyncSessionLocal() as db:
            applied = await ExecutionRepository(db).mark_terminal_if_not(ex_id, "failed")
        assert applied is False
        assert await _status(ex_id) == "completed"  # untouched
    finally:
        await _cleanup(ex_id)
        await _drop_user(user_id)


@pytest.mark.anyio
async def test_reaper_fails_only_stale_running_executions():
    if not await _db_available():
        pytest.skip("Postgres unavailable")
    wf_id, user_id = await _seed_workflow()
    old = await _make_execution(wf_id, "running", datetime.now(UTC) - timedelta(hours=2))
    fresh = await _make_execution(wf_id, "running", datetime.now(UTC))
    done = await _make_execution(wf_id, "completed", datetime.now(UTC) - timedelta(hours=2))
    try:
        async with AsyncSessionLocal() as db:
            reaped = await ExecutionRepository(db).reap_stale_running(60 * 30)
        assert old in reaped
        assert fresh not in reaped  # under the cutoff
        assert done not in reaped  # already terminal
        assert await _status(old) == "failed"
        assert await _status(fresh) == "running"
        assert await _status(done) == "completed"
    finally:
        for i in (old, fresh, done):
            await _cleanup(i)
        await _drop_user(user_id)
