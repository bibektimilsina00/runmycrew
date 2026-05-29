"""Live integration test for the real execution path.

Seeds a workflow + execution in the actual database, runs the real worker
coroutine (_run_workflow) against live Postgres + Redis, and asserts the
Execution row reaches `completed` with the expected output and logs.

This is the test that would have caught the broken-worker regression at the
transport level (not just imports). Skips automatically if the database isn't
reachable, so it stays green locally without `docker compose up db redis`.
Requires: ENCRYPTION_KEY in env (already in .env); db + redis services.
"""

import uuid

import pytest
from sqlalchemy import delete, select, text

from apps.api.app.core.database import AsyncSessionLocal
from apps.api.app.features.executions.models import Execution, ExecutionLog
from apps.api.app.features.users.models import User
from apps.api.app.features.workflows.models import Workflow
from apps.api.app.features.workspaces.models import Workspace
from apps.worker.app.jobs.tasks import _run_workflow


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


@pytest.mark.anyio
async def test_live_workflow_execution_completes():
    if not await _db_available():
        pytest.skip("requires Postgres (run: make db-up)")

    suffix = uuid.uuid4().hex[:8]
    uid, wsid, wfid, exid = (uuid.uuid4() for _ in range(4))
    graph = {
        "nodes": [
            {
                "id": "n1",
                "type": "logic.code",
                "data": {"properties": {"language": "python", "code": "output = {'sum': 2 + 3}"}},
            },
        ],
        "edges": [],
    }

    async with AsyncSessionLocal() as db:
        db.add(User(id=uid, email=f"e2e-{suffix}@test.local", hashed_password="x"))
        db.add(Workspace(id=wsid, name="e2e", slug=f"e2e-{suffix}", owner_id=uid))
        db.add(Workflow(id=wfid, name="e2e wf", graph=graph, user_id=uid, workspace_id=wsid))
        db.add(
            Execution(
                id=exid, workflow_id=wfid, status="pending", trigger_type="manual", input_data={}
            )
        )
        await db.commit()

    try:
        # Drive the real worker coroutine end-to-end (DB + Redis + engine + node).
        await _run_workflow(
            execution_id=str(exid), workflow_id=str(wfid), graph=graph, trigger_data={}
        )

        async with AsyncSessionLocal() as db:
            execution = await db.get(Execution, exid)
            assert execution is not None
            assert execution.status == "completed"
            assert execution.output_data is not None
            assert execution.output_data.get("sum") == 5

            logs = (
                (await db.execute(select(ExecutionLog).where(ExecutionLog.execution_id == exid)))
                .scalars()
                .all()
            )
            assert any("completed" in log.message.lower() for log in logs)
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Execution).where(Execution.workflow_id == wfid))
            await db.execute(delete(Workflow).where(Workflow.id == wfid))
            await db.execute(delete(Workspace).where(Workspace.id == wsid))
            await db.execute(delete(User).where(User.id == uid))
            await db.commit()
