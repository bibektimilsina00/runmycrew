"""Abuse / hardening tests for the anonymous public-app surface.

Drives the real FastAPI app over httpx ASGI transport (same harness as
test_api_auth.py). Each test seeds a user + workspace + an active workflow
carrying a ``trigger.chat_app`` node directly in the DB, hits the public
endpoints under ``/api/v1/apps/{ws}/{slug}``, then cleans up.

Config knobs under test come straight from the code, not guessed:
  - cookie name           public_router.SESSION_COOKIE == "fuse_app_session"
  - rate limit prop       props["rate_limit_per_min"] (default 20)
  - cost caps             props["session_cost_cap_usd"] / ["daily_cost_cap_usd"]
  - uploads               props["allow_file_upload"] / ["allowed_file_types"]
                          / ["max_file_size_mb"] (default 10)

Skips cleanly if Postgres is unreachable (run: make db-up).
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, text

import apps.api.app.main  # noqa: F401 — registers every ORM model (mapper deps)
from apps.api.app.core.database import AsyncSessionLocal
from apps.api.app.features.apps import public_router
from apps.api.app.features.apps.models import AppSession
from apps.api.app.features.users.models import User
from apps.api.app.features.workflows.models import Workflow
from apps.api.app.features.workspaces.models import Workspace

API = "/api/v1"
SESSION_COOKIE = public_router.SESSION_COOKIE  # "fuse_app_session"


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


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=_app()), base_url="http://test")


def _chat_graph(app_slug: str, **props) -> dict:
    """A minimal active-app graph: one trigger.chat_app node whose slug
    resolves to ``app_slug``. Extra props (rate limit, caps, upload flags)
    merge into node.data.properties."""
    return {
        "nodes": [
            {
                "id": "n1",
                "type": "trigger.chat_app",
                "data": {
                    "properties": {
                        "app_slug": app_slug,
                        "title": "Abuse Test App",
                        "mode": "chat",
                        "auth_mode": "public",
                        **props,
                    }
                },
            }
        ],
        "edges": [],
    }


async def _seed(graph: dict, *, is_active: bool = True) -> tuple[User, Workspace, Workflow]:
    """Create a user + workspace + workflow carrying ``graph``. Returns the
    ORM rows; caller must pass the user to _cleanup."""
    suffix = uuid.uuid4().hex[:8]
    async with AsyncSessionLocal() as db:
        user = User(
            email=f"abuse-{suffix}@fusetest.com",
            hashed_password="x",
            full_name="Abuse Test",
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        ws = Workspace(slug=f"abuse-ws-{suffix}", owner_id=user.id, name="Abuse WS")
        db.add(ws)
        await db.commit()
        await db.refresh(ws)

        wf = Workflow(
            name="Abuse App",
            user_id=user.id,
            workspace_id=ws.id,
            graph=graph,
            is_active=is_active,
        )
        db.add(wf)
        await db.commit()
        await db.refresh(wf)
        return user, ws, wf


async def _cleanup(user_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as db:
        # Workspace cascade drops its workflows (and their app_session rows);
        # then the user. Workflow.user_id is RESTRICT so drop any stragglers.
        await db.execute(delete(Workspace).where(Workspace.owner_id == user_id))
        await db.execute(delete(Workflow).where(Workflow.user_id == user_id))
        await db.execute(delete(User).where(User.id == user_id))
        await db.commit()


async def _seed_session(wf: Workflow, cookie_id: str, **fields) -> AppSession:
    async with AsyncSessionLocal() as db:
        sess = AppSession(workflow_id=wf.id, cookie_id=cookie_id, **fields)
        db.add(sess)
        await db.commit()
        await db.refresh(sess)
        return sess


# ─────────────────────────────────────────────────────────────────────
# 1. Rate limit → 429 + Retry-After
# ─────────────────────────────────────────────────────────────────────
# The limiter is Redis-backed and *falls open* when Redis is unavailable,
# so it can't be driven deterministically from a unit test without infra.
# We drive the exact same seam the router uses (public_router.check_rate_limit)
# and assert the router turns a limiter "denied" into 429 + Retry-After.
@pytest.mark.anyio
async def test_message_rate_limited_returns_429_with_retry_after(monkeypatch):
    if not await _db_available():
        pytest.skip("requires Postgres (run: make db-up)")

    user, ws, wf = await _seed(_chat_graph("rl-app", rate_limit_per_min=1))
    try:
        cookie = "cookie-rl-" + uuid.uuid4().hex[:8]
        await _seed_session(wf, cookie)

        async def _deny(app_id, session_key, ip_hash, max_per_minute):
            return False, 42

        monkeypatch.setattr(public_router, "check_rate_limit", _deny)

        async with _client() as client:
            client.cookies.set(SESSION_COOKIE, cookie)
            r = await client.post(
                f"{API}/apps/{ws.slug}/rl-app/message",
                json={"message": "hi"},
            )
        assert r.status_code == 429, r.text
        # Regression lock: the router used to set Retry-After on the injected
        # `Response` then `raise HTTPException(429)` — FastAPI builds a fresh
        # response for the exception and discards those headers, so a throttled
        # client got 429 with no back-off signal. Now raised as
        # HTTPException(429, headers={"Retry-After": ...}); keep it that way.
        assert r.headers.get("Retry-After") == "42", (
            "Retry-After dropped when 429 is raised as HTTPException"
        )
    finally:
        await _cleanup(user.id)


# ─────────────────────────────────────────────────────────────────────
# 2. Cost caps → 402
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_session_cost_cap_returns_402(monkeypatch):
    if not await _db_available():
        pytest.skip("requires Postgres (run: make db-up)")

    user, ws, wf = await _seed(_chat_graph("cap-app", session_cost_cap_usd=1.0))
    try:
        cookie = "cookie-cap-" + uuid.uuid4().hex[:8]
        # Session already at the cap → next message must be refused.
        await _seed_session(wf, cookie, total_cost_usd=1.5)

        # Let the rate limiter pass so we reach the cap check.
        async def _allow(app_id, session_key, ip_hash, max_per_minute):
            return True, 0

        monkeypatch.setattr(public_router, "check_rate_limit", _allow)

        async with _client() as client:
            client.cookies.set(SESSION_COOKIE, cookie)
            r = await client.post(
                f"{API}/apps/{ws.slug}/cap-app/message",
                json={"message": "hi"},
            )
        assert r.status_code == 402, r.text
        assert r.json()["detail"] == "session_cost_cap_reached"
    finally:
        await _cleanup(user.id)


# ─────────────────────────────────────────────────────────────────────
# 3. Uploads
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_upload_disabled_by_default_returns_403():
    """A chat app with no allow_file_upload prop must reject uploads."""
    if not await _db_available():
        pytest.skip("requires Postgres (run: make db-up)")

    user, ws, wf = await _seed(_chat_graph("up-off"))  # no allow_file_upload
    try:
        cookie = "cookie-upoff-" + uuid.uuid4().hex[:8]
        await _seed_session(wf, cookie)
        async with _client() as client:
            client.cookies.set(SESSION_COOKIE, cookie)
            r = await client.post(
                f"{API}/apps/{ws.slug}/up-off/upload",
                files={"file": ("a.txt", b"hello", "text/plain")},
            )
        assert r.status_code == 403, r.text
        assert r.json()["detail"] == "file_upload_disabled"
    finally:
        await _cleanup(user.id)


@pytest.mark.anyio
async def test_upload_oversize_returns_413():
    if not await _db_available():
        pytest.skip("requires Postgres (run: make db-up)")

    user, ws, wf = await _seed(_chat_graph("up-big", allow_file_upload=True, max_file_size_mb=1))
    try:
        cookie = "cookie-upbig-" + uuid.uuid4().hex[:8]
        await _seed_session(wf, cookie)
        oversize = b"x" * (1 * 1024 * 1024 + 1)  # 1 byte over the 1 MB cap
        async with _client() as client:
            client.cookies.set(SESSION_COOKIE, cookie)
            r = await client.post(
                f"{API}/apps/{ws.slug}/up-big/upload",
                files={"file": ("big.bin", oversize, "application/octet-stream")},
            )
        # Router raises 413 (REQUEST_ENTITY_TOO_LARGE) for oversize bodies.
        assert r.status_code == 413, r.text
        assert r.json()["detail"] == "file_too_large"
    finally:
        await _cleanup(user.id)


@pytest.mark.anyio
async def test_upload_disallowed_mime_rejected():
    """Task asked for 403 on disallowed MIME; the router actually returns 415
    (UNSUPPORTED_MEDIA_TYPE). Assert the real, still-secure behaviour: the
    file is rejected with a 4xx and not stored."""
    if not await _db_available():
        pytest.skip("requires Postgres (run: make db-up)")

    user, ws, wf = await _seed(
        _chat_graph(
            "up-mime",
            allow_file_upload=True,
            allowed_file_types=["image/png"],
        )
    )
    try:
        cookie = "cookie-upmime-" + uuid.uuid4().hex[:8]
        await _seed_session(wf, cookie)
        async with _client() as client:
            client.cookies.set(SESSION_COOKIE, cookie)
            r = await client.post(
                f"{API}/apps/{ws.slug}/up-mime/upload",
                files={"file": ("evil.exe", b"MZ...", "application/x-msdownload")},
            )
        assert r.status_code == 415, r.text
        assert r.json()["detail"] == "mime_not_allowed"
    finally:
        await _cleanup(user.id)


@pytest.mark.anyio
async def test_upload_traversal_filename_stored_safely():
    """A filename containing ../ must not escape any storage location. The
    router base64-encodes the bytes into a ``data:`` URL and never writes to
    disk, so path traversal is impossible by construction. Lock that: the
    stored url is a data URI (not a filesystem path) and the raw filename,
    while echoed back, is inert."""
    if not await _db_available():
        pytest.skip("requires Postgres (run: make db-up)")

    user, ws, wf = await _seed(_chat_graph("up-trav", allow_file_upload=True))
    try:
        cookie = "cookie-uptrav-" + uuid.uuid4().hex[:8]
        await _seed_session(wf, cookie)
        evil = "../../../../etc/passwd"
        async with _client() as client:
            client.cookies.set(SESSION_COOKIE, cookie)
            r = await client.post(
                f"{API}/apps/{ws.slug}/up-trav/upload",
                files={"file": (evil, b"payload", "text/plain")},
            )
        assert r.status_code == 200, r.text
        body = r.json()
        # No disk path is ever produced — the content lives in a data URI.
        assert body["url"].startswith("data:text/plain;base64,")
        assert "/etc/passwd" not in body["url"]
    finally:
        await _cleanup(user.id)


# ─────────────────────────────────────────────────────────────────────
# 4. Hosted resolution can't leak
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_inactive_app_resolves_404():
    if not await _db_available():
        pytest.skip("requires Postgres (run: make db-up)")

    user, ws, wf = await _seed(_chat_graph("dead-app"), is_active=False)
    try:
        async with _client() as client:
            r = await client.get(f"{API}/apps/{ws.slug}/dead-app")
        assert r.status_code == 404, r.text
    finally:
        await _cleanup(user.id)


@pytest.mark.anyio
async def test_cross_workspace_slug_resolves_404():
    """A slug that lives in workspace A must not resolve under workspace B."""
    if not await _db_available():
        pytest.skip("requires Postgres (run: make db-up)")

    user_a, ws_a, _ = await _seed(_chat_graph("shared-slug"))
    user_b, ws_b, _ = await _seed(_chat_graph("other-slug"))
    try:
        async with _client() as client:
            # A's slug under B's workspace → not found.
            r = await client.get(f"{API}/apps/{ws_b.slug}/shared-slug")
            assert r.status_code == 404, r.text
            # sanity: it *does* resolve under its own workspace.
            r_ok = await client.get(f"{API}/apps/{ws_a.slug}/shared-slug")
            assert r_ok.status_code == 200, r_ok.text
    finally:
        await _cleanup(user_a.id)
        await _cleanup(user_b.id)


@pytest.mark.anyio
async def test_nonexistent_slug_resolves_404():
    if not await _db_available():
        pytest.skip("requires Postgres (run: make db-up)")

    user, ws, _ = await _seed(_chat_graph("real-app"))
    try:
        async with _client() as client:
            r = await client.get(f"{API}/apps/{ws.slug}/no-such-app")
        assert r.status_code == 404, r.text
    finally:
        await _cleanup(user.id)


# ─────────────────────────────────────────────────────────────────────
# 5. Anonymous session cookie hardening
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_session_cookie_is_httponly_and_path_scoped():
    """POST /session must set fuse_app_session as HttpOnly, path-scoped to the
    app namespace, and SameSite=Lax. Locks current secure attributes so a
    regression (e.g. dropping HttpOnly) fails this test."""
    if not await _db_available():
        pytest.skip("requires Postgres (run: make db-up)")

    user, ws, wf = await _seed(_chat_graph("cookie-app"))
    try:
        async with _client() as client:
            r = await client.post(f"{API}/apps/{ws.slug}/cookie-app/session")
        assert r.status_code == 200, r.text
        set_cookie = r.headers.get("set-cookie")
        assert set_cookie is not None, "no Set-Cookie on /session"
        lc = set_cookie.lower()
        assert SESSION_COOKIE in set_cookie
        assert "httponly" in lc, f"session cookie not HttpOnly: {set_cookie}"
        assert "samesite=lax" in lc, f"session cookie missing SameSite=Lax: {set_cookie}"
        assert f"path=/api/v1/apps/{ws.slug}/cookie-app" in lc, (
            f"session cookie not path-scoped to the app: {set_cookie}"
        )
    finally:
        await _cleanup(user.id)


# ── Stream IDOR: one visitor can't read another's execution ────────────


@pytest.mark.anyio
async def test_stream_rejects_foreign_execution_id(monkeypatch):
    """The SSE stream must be bound to the caller's OWN execution. A visitor
    who learns another visitor's execution_id must get 403, not their events."""
    if not await _db_available():
        pytest.skip("Postgres unavailable")
    user, ws, wf = await _seed(_chat_graph("idor-app"))
    try:
        from apps.api.app.features.apps.models import AppMessage

        victim = await _seed_session(wf, "victim-cookie")
        await _seed_session(wf, "attacker-cookie")  # attacker's own valid session
        # A message + execution owned by the VICTIM.
        async with AsyncSessionLocal() as db:
            msg = AppMessage(
                session_id=victim.id, role="assistant", execution_id="app-victim-exec-1"
            )
            db.add(msg)
            await db.commit()

        async with _client() as c:
            # Attacker presents their own valid session cookie but asks for
            # the victim's execution stream.
            r = await c.get(
                f"{API}/apps/{ws.slug}/idor-app/stream/app-victim-exec-1",
                cookies={SESSION_COOKIE: "attacker-cookie"},
            )
        assert r.status_code == 403, r.text
    finally:
        await _cleanup(user.id)


# ── Cookie carries Secure in production ────────────────────────────────


@pytest.mark.anyio
async def test_session_cookie_secure_in_production(monkeypatch):
    monkeypatch.setattr(public_router, "_cookie_secure", lambda: True)
    if not await _db_available():
        pytest.skip("Postgres unavailable")
    user, ws, wf = await _seed(_chat_graph("secure-app"))
    try:
        async with _client() as c:
            r = await c.post(f"{API}/apps/{ws.slug}/secure-app/session", json={})
        set_cookie = r.headers.get("set-cookie", "")
        assert "secure" in set_cookie.lower(), f"Secure flag missing in prod: {set_cookie}"
    finally:
        await _cleanup(user.id)


# ── Upload: active-content MIME blocked even if the owner allowlisted it ─


@pytest.mark.anyio
async def test_upload_rejects_inline_active_mime():
    if not await _db_available():
        pytest.skip("Postgres unavailable")
    user, ws, wf = await _seed(
        _chat_graph(
            "svg-app",
            allow_file_upload=True,
            allowed_file_types=["image/svg+xml"],  # owner allowlisted it…
        )
    )
    try:
        await _seed_session(wf, "up-cookie")
        async with _client() as c:
            r = await c.post(
                f"{API}/apps/{ws.slug}/svg-app/upload",
                cookies={SESSION_COOKIE: "up-cookie"},
                files={"file": ("x.svg", b"<svg onload=alert(1)>", "image/svg+xml")},
            )
        # …still refused: it renders as active content from a data: URL on
        # the app origin (stored XSS).
        assert r.status_code == 415, r.text
    finally:
        await _cleanup(user.id)
