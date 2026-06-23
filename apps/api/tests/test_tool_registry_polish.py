"""Phase 4 tests — tool registry polish.

Covers:
- new ToolDefinition fields (category, tags, dangerous)
- to_json_catalog() with filters
- to_anthropic_schema() output shape
- rate-limit hook short-circuits execute()
- catalog endpoint serialises the new fields
"""

from __future__ import annotations

import httpx
import pytest

from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.tools.base import (
    ToolDefinition,
    ToolOAuth,
    ToolParam,
    ToolResult,
)
from apps.api.app.node_system.tools.registry import ToolRegistry


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _ctx() -> NodeContext:
    # Minimal stub — registry only reads workspace_id/credentials.
    return NodeContext(
        execution_id="run_1",
        workflow_id="wf_1",
        node_id="agent_1",
        variables={},
        credentials=[],
        http_client=httpx.AsyncClient(),
        workspace_id="ws_xyz",
    )


def _make_registry() -> ToolRegistry:
    reg = ToolRegistry()

    async def _ok_exec(params, ctx):
        return ToolResult(success=True, output={"ok": True})

    reg.register(
        ToolDefinition(
            id="linear_update_issue",
            name="Update Linear issue",
            description="Update issue state, assignee, or comments.",
            params={
                "id": ToolParam(type="string", required=True, description="Issue id"),
            },
            oauth=ToolOAuth(required=True, credential_type="linear"),
            category="linear",
            tags=["write", "linear"],
            dangerous=True,
        ),
        _ok_exec,
    )
    reg.register(
        ToolDefinition(
            id="linear_list_issues",
            name="List Linear issues",
            description="Search/filter issues.",
            params={
                "queue": ToolParam(type="string", required=False, description="Queue name"),
            },
            oauth=ToolOAuth(required=True, credential_type="linear"),
            category="linear",
            tags=["read", "linear"],
            dangerous=False,
        ),
        _ok_exec,
    )
    return reg


# ── Definition / catalog ───────────────────────────────────────────


def test_definition_carries_new_fields():
    reg = _make_registry()
    defn = reg.get_definition("linear_update_issue")
    assert defn is not None
    assert defn.category == "linear"
    assert defn.tags == ["write", "linear"]
    assert defn.dangerous is True


def test_to_json_catalog_default_lists_all():
    reg = _make_registry()
    catalog = reg.to_json_catalog()
    ids = [e["id"] for e in catalog]
    assert ids == ["linear_list_issues", "linear_update_issue"]
    # Catalog entries expose the loop-hardening fields verbatim.
    update_entry = next(e for e in catalog if e["id"] == "linear_update_issue")
    assert update_entry["dangerous"] is True
    assert "write" in update_entry["tags"]
    assert update_entry["oauth_required"] is True
    assert update_entry["credential_type"] == "linear"


def test_to_json_catalog_filter_by_tag():
    reg = _make_registry()
    write_only = reg.to_json_catalog(tag="write")
    assert [e["id"] for e in write_only] == ["linear_update_issue"]


def test_to_json_catalog_filter_by_category():
    reg = _make_registry()
    catalog = reg.to_json_catalog(category="linear")
    assert len(catalog) == 2
    assert reg.to_json_catalog(category="nope") == []


def test_list_categories_dedupes():
    reg = _make_registry()
    assert reg.list_categories() == ["linear"]


# ── Anthropic schema ───────────────────────────────────────────────


def test_to_anthropic_schema_shape():
    reg = _make_registry()
    schema = reg.to_anthropic_schema("linear_update_issue")
    assert schema is not None
    assert schema["name"] == "linear_update_issue"
    assert "description" in schema
    assert schema["input_schema"]["type"] == "object"
    assert "id" in schema["input_schema"]["properties"]
    assert schema["input_schema"]["required"] == ["id"]


def test_to_anthropic_schema_unknown_returns_none():
    reg = _make_registry()
    assert reg.to_anthropic_schema("nope") is None


# ── Rate-limit hook ────────────────────────────────────────────────


@pytest.mark.anyio
async def test_rate_limit_hook_allows():
    reg = _make_registry()
    seen: list[tuple[str, str]] = []

    async def allow(workspace_id: str, tool_id: str, ctx):
        seen.append((workspace_id, tool_id))
        return True

    reg.set_rate_limit_check(allow)
    result = await reg.execute(
        "linear_update_issue",
        {"id": "ENG-1"},
        _ctx_with_creds(),
    )
    assert result.success is True
    assert seen == [("ws_xyz", "linear_update_issue")]


@pytest.mark.anyio
async def test_rate_limit_hook_denies_short_circuits():
    reg = _make_registry()
    called = False

    async def deny(workspace_id: str, tool_id: str, ctx):
        return False

    async def mark_called(params, ctx):
        nonlocal called
        called = True
        return ToolResult(success=True)

    # Override the underlying executor so we can detect short-circuit.
    reg._executors["linear_update_issue"] = mark_called  # noqa: SLF001
    reg.set_rate_limit_check(deny)

    result = await reg.execute(
        "linear_update_issue",
        {"id": "ENG-1"},
        _ctx_with_creds(),
    )
    assert result.success is False
    assert "Rate limit" in (result.error or "")
    assert called is False  # executor never reached


@pytest.mark.anyio
async def test_no_hook_means_no_gate():
    reg = _make_registry()
    result = await reg.execute(
        "linear_update_issue",
        {"id": "ENG-1"},
        _ctx_with_creds(),
    )
    assert result.success is True


def _ctx_with_creds() -> NodeContext:
    ctx = _ctx()
    ctx.credentials = [
        {"id": "cred_1", "type": "linear", "data": {"access_token": "tok_abc"}},
    ]
    return ctx
