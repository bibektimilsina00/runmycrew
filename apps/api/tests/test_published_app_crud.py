"""API-level test for publish → session → history flow.

Register → login → create workflow with trigger.chat_app → publish → hit
public config → create session → send message → (worker mocked)
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select, text

from apps.api.app.core.database import AsyncSessionLocal
from apps.api.app.features.apps.models import PublishedApp
from apps.api.app.features.users.models import User
from apps.api.app.features.workflows.models import Workflow
from apps.api.app.features.workspaces.models import Workspace

API = "/api/v1"


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


def _app():
    from apps.api.app.main import app

    return app


@pytest.mark.anyio
async def test_publish_session_history_flow():
    if not await _db_available():
        pytest.skip("requires Postgres")

    email = f"apptest-{uuid.uuid4().hex[:8]}@fusetest.com"
    password = "password12345"
    workflow_id: uuid.UUID | None = None

    try:
        transport = ASGITransport(app=_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post(
                f"{API}/auth/register",
                json={"email": email, "password": password, "full_name": "App Test"},
            )
            assert r.status_code in (200, 201), r.text

            r = await client.post(f"{API}/auth/login", json={"email": email, "password": password})
            assert r.status_code == 200, r.text
            token = r.json()["access_token"]
            auth = {"Authorization": f"Bearer {token}"}

            # Grab workspace slug
            r = await client.get(f"{API}/workspaces/", headers=auth)
            assert r.status_code == 200, r.text
            workspace_slug = r.json()[0]["slug"]

            # Build a workflow with a trigger.chat_app node
            graph = {
                "nodes": [
                    {
                        "id": "n1",
                        "type": "trigger.chat_app",
                        "position": {"x": 0, "y": 0},
                        "data": {
                            "label": "Chat App",
                            "properties": {
                                "title": "Test Bot",
                                "app_slug": "test-bot",
                                "mode": "chat",
                                "welcome_message": "Hi!",
                            },
                        },
                    },
                ],
                "edges": [],
            }
            r = await client.post(
                f"{API}/workflows/",
                json={"name": "Test Bot Workflow", "graph": graph},
                headers=auth,
            )
            assert r.status_code in (200, 201), r.text
            workflow_id = uuid.UUID(r.json()["id"])

            # Publish
            r = await client.post(
                f"{API}/workflows/{workflow_id}/publish",
                json={"title": "Test Bot"},
                headers=auth,
            )
            assert r.status_code == 201, r.text
            published = r.json()
            assert published["app_slug"] == "test-bot"
            assert published["version_num"] == 1
            assert published["is_active"] is True

            # Hit the public config (no auth cookie yet)
            r = await client.get(f"{API}/apps/{workspace_slug}/test-bot")
            assert r.status_code == 200, r.text
            pub = r.json()
            assert pub["title"] == "Test Bot"
            assert pub["mode"] == "chat"
            # Sensitive fields must not leak.
            assert "graph_snapshot" not in pub
            assert "password_hash" not in pub

            # Create session (sets cookie)
            r = await client.post(f"{API}/apps/{workspace_slug}/test-bot/session")
            assert r.status_code == 200, r.text
            env = r.json()
            assert env["session"]["message_count"] == 0
            assert env["messages"] == []

            # Second call returns same session id.
            r2 = await client.post(f"{API}/apps/{workspace_slug}/test-bot/session")
            assert r2.status_code == 200, r2.text
            assert r2.json()["session"]["id"] == env["session"]["id"]

            # Re-publish → version bumps
            r = await client.post(
                f"{API}/workflows/{workflow_id}/publish",
                json={"title": "Test Bot v2"},
                headers=auth,
            )
            assert r.status_code == 201, r.text
            assert r.json()["version_num"] == 2

            # Versions list
            r = await client.get(
                f"{API}/workflows/{workflow_id}/app/versions",
                headers=auth,
            )
            assert r.status_code == 200
            assert len(r.json()) == 2

            # Unpublish
            r = await client.delete(f"{API}/workflows/{workflow_id}/publish", headers=auth)
            assert r.status_code == 204

            r = await client.get(f"{API}/apps/{workspace_slug}/test-bot")
            assert r.status_code == 404
    finally:
        await _cleanup(email, workflow_id)


async def _cleanup(email: str, workflow_id: uuid.UUID | None) -> None:
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if not user:
            return
        await db.execute(delete(PublishedApp).where(PublishedApp.published_by == user.id))
        if workflow_id:
            await db.execute(delete(Workflow).where(Workflow.id == workflow_id))
        await db.execute(delete(Workspace).where(Workspace.owner_id == user.id))
        await db.execute(delete(Workflow).where(Workflow.user_id == user.id))
        await db.execute(delete(User).where(User.id == user.id))
        await db.commit()
