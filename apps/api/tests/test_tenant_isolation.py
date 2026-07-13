"""Cross-tenant authorization test (table-driven).

Two users live in two separate personal workspaces. User A creates one object
under each authenticated, workspace-scoped resource. User B — a different user
in a different workspace — then tries to access every one of A's object ids and
must be refused (403/404) on all of them, never 200-with-A's-data.

Also included: a route-count drift guard that enumerates the FastAPI app's
registered workspace-scoped GET-by-id routes and asserts each is either covered
by the isolation table or on an explicit allowlist with a reason — so a new
object router can't be added without a conscious isolation decision.

Run: ./.venv/bin/pytest apps/api/tests/test_tenant_isolation.py -q
"""

import re
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select, text

from apps.api.app.core.database import AsyncSessionLocal
from apps.api.app.features.executions.models import Execution
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


# ── Actor helper ──────────────────────────────────────────────────────────────


@dataclass
class Actor:
    """A registered+logged-in user with their default (personal) workspace.

    B never sends an X-Workspace-ID header, so every request resolves to B's own
    workspace — the realistic cross-tenant case where B asks for A's object id
    while scoped to B's tenant.
    """

    email: str
    token: str

    @property
    def auth(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


async def _register_login(client: AsyncClient, tag: str) -> Actor:
    email = f"isotest-{tag}-{uuid.uuid4().hex[:8]}@fusetest.com"
    password = "password12345"
    r = await client.post(
        f"{API}/auth/register",
        json={"email": email, "password": password, "full_name": f"Iso {tag}"},
    )
    assert r.status_code in (200, 201), r.text
    r = await client.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return Actor(email=email, token=r.json()["access_token"])


# ── Resource descriptors ──────────────────────────────────────────────────────


@dataclass
class Resource:
    name: str
    # Given A's client + auth headers and shared context, create one object and
    # return its id (as a string). May stash context (e.g. workflow_id) into ctx.
    create: Callable[[AsyncClient, "Actor", dict], Awaitable[str]]
    # GET-by-id (or per-object access) path template, "{id}" substituted.
    access_path: str
    # HTTP method for the access probe (default GET; a few resources have no
    # read-by-id, so we probe the workspace-scoped mutation instead).
    method: str = "GET"
    # Optional body for non-GET probes.
    body: dict[str, Any] | None = None


async def _post_id(client, actor, path, payload, id_field="id") -> str:
    r = await client.post(f"{API}{path}", json=payload, headers=actor.auth)
    assert r.status_code in (200, 201), f"create {path} failed: {r.status_code} {r.text}"
    return str(r.json()[id_field])


async def _create_workflow(client, actor, ctx) -> str:
    wid = await _post_id(client, actor, "/workflows/", {"name": "A's workflow"})
    ctx["workflow_id"] = wid
    return wid


async def _create_crew(client, actor, ctx) -> str:
    return await _post_id(client, actor, "/crews/", {"name": "A's crew"})


async def _create_persona(client, actor, ctx) -> str:
    return await _post_id(
        client,
        actor,
        "/personas/",
        {
            "name": "A's persona",
            "role": "reviewer",
            "description": "x",
            "system_prompt": "You review.",
            "default_provider": "anthropic",
            "default_model": "claude-sonnet-4-6",
            "tools": [],
            "color": "#f43f5e",
            "icon_slug": "Shield",
            "temperature": 0.1,
            "max_iterations": 6,
        },
    )


async def _create_skill(client, actor, ctx) -> str:
    return await _post_id(client, actor, "/skills/", {"name": "A's skill"})


async def _create_folder(client, actor, ctx) -> str:
    return await _post_id(client, actor, "/folders/", {"name": "A's folder"})


async def _create_kb(client, actor, ctx) -> str:
    return await _post_id(client, actor, "/kb/", {"name": "A's KB"})


async def _create_table(client, actor, ctx) -> str:
    return await _post_id(client, actor, "/tables/", {"name": "A's table"})


async def _create_credential(client, actor, ctx) -> str:
    return await _post_id(
        client,
        actor,
        "/credentials/",
        {"name": "A's key", "type": "openai", "data": {"api_key": "sk-test-isolation"}},
    )


async def _create_secret(client, actor, ctx) -> str:
    return await _post_id(
        client, actor, "/secrets/", {"name": "A_SECRET", "value": "shh", "is_secret": True}
    )


async def _create_execution(client, actor, ctx) -> str:
    """Insert an Execution row directly under A's workflow.

    Running the engine (POST /workflows/{id}/run) would need a real graph and
    LLM calls; the isolation boundary we're testing is get_by_id_and_workspace
    on the execution's workflow, so a bare row under A's workflow is enough.
    """
    workflow_id = ctx.get("workflow_id")
    assert workflow_id, "execution resource requires the workflow resource to run first"
    async with AsyncSessionLocal() as db:
        ex = Execution(workflow_id=uuid.UUID(workflow_id), status="success", trigger_type="manual")
        db.add(ex)
        await db.commit()
        return str(ex.id)


async def _create_app_workflow(client, actor, ctx) -> str:
    """App owner endpoints scope by the underlying workflow. Reuse A's workflow;
    no AppSession row is needed because _get_workflow 404s before any session
    lookup when B (wrong workspace) requests it."""
    wid = ctx.get("workflow_id")
    if not wid:
        wid = await _create_workflow(client, actor, ctx)
    return wid


# Order matters: workflow first so execution + app-owner can reuse its id.
RESOURCES: list[Resource] = [
    Resource("workflows", _create_workflow, "/workflows/{id}"),
    Resource("crews", _create_crew, "/crews/{id}"),
    Resource("personas", _create_persona, "/personas/{id}"),
    Resource("skills", _create_skill, "/skills/{id}"),
    Resource("folders", _create_folder, "/folders/{id}"),
    Resource("knowledge", _create_kb, "/kb/{id}"),
    Resource("tables", _create_table, "/tables/{id}/rows"),
    Resource("executions", _create_execution, "/executions/{id}"),
    # No read-by-id route; the workspace-scoped per-object access is reveal (GET).
    Resource("secrets", _create_secret, "/secrets/{id}/reveal"),
    # No read-by-id route; PATCH rename is the workspace-scoped per-object access.
    Resource(
        "credentials",
        _create_credential,
        "/credentials/{id}",
        method="PATCH",
        body={"name": "B renamed it"},
    ),
    # App owner sessions list: scoped by the owning workflow's workspace.
    Resource("apps_owner_sessions", _create_app_workflow, "/workflows/{id}/app/sessions"),
]


async def _probe(client: AsyncClient, res: Resource, obj_id: str, actor: Actor):
    path = f"{API}{res.access_path.format(id=obj_id)}"
    if res.method == "GET":
        return await client.get(path, headers=actor.auth)
    if res.method == "PATCH":
        return await client.patch(path, json=res.body or {}, headers=actor.auth)
    raise AssertionError(f"unhandled probe method {res.method}")


@pytest.mark.anyio
async def test_cross_tenant_isolation():
    if not await _db_available():
        pytest.skip("requires Postgres (run: make db-up)")

    a_email = b_email = None
    try:
        transport = ASGITransport(app=_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            a = await _register_login(client, "a")
            b = await _register_login(client, "b")
            a_email, b_email = a.email, b.email

            ctx: dict[str, Any] = {}
            leaks: list[str] = []

            for res in RESOURCES:
                obj_id = await res.create(client, a, ctx)

                # Sanity: the object really exists and A can reach it. Without
                # this a leak test could pass on a 404-because-missing.
                a_resp = await _probe(client, res, obj_id, a)
                assert a_resp.status_code in (
                    200,
                    201,
                ), (
                    f"[{res.name}] owner A could not access own object: {a_resp.status_code} {a_resp.text}"
                )

                # B (different workspace) must be refused.
                b_resp = await _probe(client, res, obj_id, b)
                if b_resp.status_code not in (403, 404):
                    leaks.append(f"{res.name}: B got {b_resp.status_code}")

            assert not leaks, "CROSS-TENANT LEAK — user B accessed user A's objects: " + "; ".join(
                leaks
            )
    finally:
        if a_email:
            await _cleanup_user(a_email)
        if b_email:
            await _cleanup_user(b_email)


# ── Templates: no private per-object GET; owner view is the /mine list ─────────


@pytest.mark.anyio
async def test_templates_mine_isolation():
    """`GET /templates/{slug_or_id}` is a public marketplace endpoint by design
    (no workspace dep — see templates/service.get_detail). The user-owned view
    is the `/mine` list, so isolation for private templates means: A's published
    template appears in A's /mine and never in B's /mine."""
    if not await _db_available():
        pytest.skip("requires Postgres (run: make db-up)")

    a_email = b_email = None
    try:
        transport = ASGITransport(app=_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            a = await _register_login(client, "a")
            b = await _register_login(client, "b")
            a_email, b_email = a.email, b.email

            wid = await _post_id(client, a, "/workflows/", {"name": "tmpl src"})
            r = await client.post(
                f"{API}/templates/publish",
                json={"workflow_id": wid, "title": "A private template", "category": "automation"},
                headers=a.auth,
            )
            assert r.status_code == 201, r.text
            tmpl_id = str(r.json()["id"])

            r = await client.get(f"{API}/templates/mine", headers=a.auth)
            assert r.status_code == 200, r.text
            assert tmpl_id in {str(t["id"]) for t in r.json()}, (
                "A's own template missing from /mine"
            )

            r = await client.get(f"{API}/templates/mine", headers=b.auth)
            assert r.status_code == 200, r.text
            assert tmpl_id not in {str(t["id"]) for t in r.json()}, (
                "CROSS-TENANT LEAK — A's template showed up in B's /mine"
            )
    finally:
        if a_email:
            await _cleanup_user(a_email)
        if b_email:
            await _cleanup_user(b_email)


# ── Route-count drift guard ────────────────────────────────────────────────────

# Every workspace-scoped GET-by-id route the isolation table covers. Format is
# the raw FastAPI path so it can be diffed against app.routes directly.
_COVERED_ROUTES = {
    "/api/v1/workflows/{workflow_id}",
    "/api/v1/crews/{crew_id}",
    "/api/v1/personas/{persona_id}",
    "/api/v1/skills/{skill_id}",
    "/api/v1/folders/{folder_id}",
    "/api/v1/kb/{kb_id}",
    "/api/v1/tables/{table_id}/rows",
    "/api/v1/executions/{execution_id}",
    "/api/v1/secrets/{secret_id}/reveal",
    "/api/v1/workflows/{workflow_id}/app/sessions",
}

# Intentionally excluded workspace-scoped-looking GET-by-id routes, each with a
# reason. A new route matching the drift filter that is neither covered nor here
# fails the guard until someone makes an isolation decision.
_EXCLUDED_ROUTES = {
    # Sub-resources of an object already covered above — isolation is enforced at
    # the parent object's workspace lookup, so covering the parent covers these.
    "/api/v1/workflows/{workflow_id}/versions": "sub-resource of workflow (parent covered)",
    "/api/v1/workflows/{workflow_id}/app/analytics": "sub-resource of workflow (parent covered)",
    "/api/v1/crews/{crew_id}/executions": "sub-resource of crew (parent covered)",
    "/api/v1/kb/{kb_id}/documents/{doc_id}/chunks": "sub-resource of KB (parent covered)",
    "/api/v1/tables/{table_id}/export.csv": "sub-resource of table (parent covered)",
    # Public / unauthenticated app-runtime endpoints (apps.public_router) — no
    # workspace membership involved; access is by workspace_slug+app_slug+secret.
    "/api/v1/apps/{workspace_slug}/{app_slug}/sessions/{session_id}": "public app runtime, not workspace-scoped",
    "/api/v1/apps/{workspace_slug}/{app_slug}/stream/{execution_id}": "public app runtime, not workspace-scoped",
    # The workspace itself is the tenant boundary — resolve_workspace already
    # require_member()s the caller, so these 403 for non-members by construction.
    "/api/v1/workspaces/{workspace_id}/members": "workspace is the tenant boundary (require_member)",
    "/api/v1/workspaces/{workspace_id}/escalation-config": "workspace is the tenant boundary (require_member)",
    # User-scoped (by current_user through workflow ownership), not workspace-
    # scoped — a different isolation mechanism, out of this table's scope.
    "/api/v1/copilot/{workflow_id}/settings": "user-scoped via workflow ownership, not workspace",
    "/api/v1/copilot/{workflow_id}/sessions": "user-scoped via workflow ownership, not workspace",
    "/api/v1/copilot/{workflow_id}/sessions/{session_id}": "user-scoped via workflow ownership, not workspace",
    "/api/v1/a2a/{workflow_id}/status/{execution_id}": "a2a protocol endpoint, own auth mechanism",
    "/api/v1/workflows/{workflow_id}/triggers/{node_id}/listen/status": "trigger listen state, keyed by workflow",
    "/api/v1/workflows/{workflow_id}/triggers/{node_id}/fixture": "trigger fixture, keyed by workflow",
    # Not tenant data.
    "/api/v1/tools/{tool_id}": "global tool catalog, not tenant data",
    "/api/v1/templates/{slug_or_id}": "public marketplace detail by design (covered via /mine test)",
    "/api/v1/webhooks/meta/{app_id}": "public webhook verification handshake",
    # Signed-URL / stats asset endpoints — access is by HMAC signature, not
    # workspace membership; view/download verify the signature, not the tenant.
    "/api/v1/assets/{asset_id}/view": "signed-URL access (HMAC), not workspace membership",
    "/api/v1/assets/{asset_id}/download": "signed-URL access (HMAC), not workspace membership",
    "/api/v1/assets/public/{asset_id}": "public asset by design",
    "/api/v1/credentials/{credential_id}/lookup/{provider}/{resource}": "hits external provider APIs; covered via credential PATCH probe",
}


def test_isolation_table_covers_workspace_scoped_routes():
    """Enumerate the app's GET-by-id routes and assert each is either covered by
    the isolation table or on the explicit allowlist. A newly added object
    router fails here until an isolation decision is recorded above."""
    app = _app()
    id_param = re.compile(r"\{[a-z_]*_id\}")

    discovered = {
        r.path
        for r in app.routes
        if "GET" in (getattr(r, "methods", None) or set())
        and id_param.search(getattr(r, "path", ""))
    }

    accounted = _COVERED_ROUTES | set(_EXCLUDED_ROUTES)
    uncovered = discovered - accounted
    assert not uncovered, (
        "New workspace-scoped GET-by-id route(s) not in the isolation table. "
        "Add each to _COVERED_ROUTES (and the RESOURCES table) or to "
        "_EXCLUDED_ROUTES with a reason:\n  " + "\n  ".join(sorted(uncovered))
    )

    # Keep the table honest: covered routes must actually exist in the app.
    stale = _COVERED_ROUTES - discovered
    assert not stale, f"_COVERED_ROUTES lists routes the app no longer has: {sorted(stale)}"


# ── Cleanup ────────────────────────────────────────────────────────────────────


async def _cleanup_user(email: str) -> None:
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if not user:
            return
        # Workflows/executions cascade via workspace FK; workspace delete removes
        # workspace-scoped rows (crews, personas, folders, kb, tables, secrets,
        # credentials, templates). Delete owned workflows explicitly too since
        # some tests key them off user_id.
        await db.execute(delete(Workspace).where(Workspace.owner_id == user.id))
        await db.execute(delete(Workflow).where(Workflow.user_id == user.id))
        await db.execute(delete(User).where(User.id == user.id))
        await db.commit()
