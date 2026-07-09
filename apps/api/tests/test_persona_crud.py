"""API-level integration test for the persona CRUD flow.

Register → login → create persona → list → update → delete. Uses the real
DB and cleans up. Skips if the DB is unreachable.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select, text

from apps.api.app.core.database import AsyncSessionLocal
from apps.api.app.features.personas.models import Persona
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
async def test_persona_crud_flow():
    if not await _db_available():
        pytest.skip("requires Postgres (run: make db-up)")

    email = f"personatest-{uuid.uuid4().hex[:8]}@fusetest.com"
    password = "password12345"

    try:
        transport = ASGITransport(app=_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post(
                f"{API}/auth/register",
                json={"email": email, "password": password, "full_name": "Persona Test"},
            )
            assert r.status_code in (200, 201), r.text

            r = await client.post(f"{API}/auth/login", json={"email": email, "password": password})
            assert r.status_code == 200, r.text
            token = r.json()["access_token"]
            auth = {"Authorization": f"Bearer {token}"}

            # Empty list on a fresh workspace
            r = await client.get(f"{API}/personas/", headers=auth)
            assert r.status_code == 200, r.text
            assert r.json() == []

            # Create
            payload = {
                "name": "Senior Reviewer",
                "role": "reviewer",
                "description": "Ships nothing that's wrong.",
                "system_prompt": "You are a strict, fair reviewer.",
                "default_provider": "anthropic",
                "default_model": "claude-sonnet-4-6",
                "tools": [],
                "color": "#f43f5e",
                "icon_slug": "Shield",
                "temperature": 0.1,
                "max_iterations": 6,
            }
            r = await client.post(f"{API}/personas/", json=payload, headers=auth)
            assert r.status_code == 201, r.text
            created = r.json()
            persona_id = created["id"]
            assert created["name"] == "Senior Reviewer"
            assert created["role"] == "reviewer"
            assert created["default_model"] == "claude-sonnet-4-6"

            # List
            r = await client.get(f"{API}/personas/", headers=auth)
            assert r.status_code == 200
            assert len(r.json()) == 1

            # Patch
            r = await client.patch(
                f"{API}/personas/{persona_id}",
                json={"description": "Updated bio.", "temperature": 0.05},
                headers=auth,
            )
            assert r.status_code == 200, r.text
            assert r.json()["description"] == "Updated bio."
            assert r.json()["temperature"] == 0.05

            # Get by id
            r = await client.get(f"{API}/personas/{persona_id}", headers=auth)
            assert r.status_code == 200
            assert r.json()["id"] == persona_id

            # Delete
            r = await client.delete(f"{API}/personas/{persona_id}", headers=auth)
            assert r.status_code == 204, r.text

            r = await client.get(f"{API}/personas/{persona_id}", headers=auth)
            assert r.status_code == 404
    finally:
        await _cleanup_user(email)


async def _cleanup_user(email: str) -> None:
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if not user:
            return
        # persona cascades via workspace; leave workflow order the same as auth test.
        await db.execute(delete(Persona).where(Persona.user_id == user.id))
        await db.execute(delete(Workspace).where(Workspace.owner_id == user.id))
        await db.execute(delete(Workflow).where(Workflow.user_id == user.id))
        await db.execute(delete(User).where(User.id == user.id))
        await db.commit()
