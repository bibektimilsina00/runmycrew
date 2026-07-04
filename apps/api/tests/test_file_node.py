"""File node — read_url / write / append / parse_text.

Covers each op's happy path plus the security-critical path-traversal
refusal and download-cap enforcement.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.nodes.common.file.file_node import (
    FileNode,
    _execution_root,
    _safe_path,
)


def _make_ctx(execution_id: str = "test-exec-1") -> NodeContext:
    return NodeContext(
        execution_id=execution_id,
        workflow_id="w1",
        node_id="n1",
        variables={},
        credentials=[],
        http_client=MagicMock(),
    )


def _make_node(**props) -> FileNode:
    return FileNode(node_id="n1", properties=props)


# ── security: path traversal ─────────────────────────────────────────


def test_safe_path_refuses_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="escapes execution root"):
        _safe_path(tmp_path, "../../etc/passwd")


def test_safe_path_refuses_absolute(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="escapes execution root"):
        _safe_path(tmp_path, "/etc/passwd")


def test_safe_path_allows_nested_relative(tmp_path: Path) -> None:
    resolved = _safe_path(tmp_path, "a/b/c.txt")
    assert resolved.is_relative_to(tmp_path)


# ── write + append ────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_write_creates_file() -> None:
    ctx = _make_ctx("wt1")
    node = _make_node(operation="write", path="hello.txt", content="hi")
    result = await node.execute({}, ctx)
    assert result.success
    written = Path(result.output_data["path"])
    assert written.exists()
    assert written.read_text() == "hi"


@pytest.mark.anyio
async def test_append_adds_to_existing_file() -> None:
    ctx = _make_ctx("wt2")
    (await _make_node(operation="write", path="log.txt", content="a").execute({}, ctx))
    result = await _make_node(operation="append", path="log.txt", content="b").execute({}, ctx)
    assert result.success
    assert Path(result.output_data["path"]).read_text() == "ab"


@pytest.mark.anyio
async def test_write_refuses_path_traversal() -> None:
    ctx = _make_ctx("wt3")
    node = _make_node(operation="write", path="../outside.txt", content="x")
    result = await node.execute({}, ctx)
    assert not result.success
    assert "escapes execution root" in (result.error or "")


# ── parse_text ────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_parse_text_json() -> None:
    ctx = _make_ctx("pt1")
    await _make_node(operation="write", path="data.json", content='{"a": 1}').execute({}, ctx)
    result = await _make_node(operation="parse_text", path="data.json").execute({}, ctx)
    assert result.success
    assert result.output_data["format"] == "json"
    assert result.output_data["parsed"] == {"a": 1}


@pytest.mark.anyio
async def test_parse_text_csv() -> None:
    ctx = _make_ctx("pt2")
    await _make_node(
        operation="write",
        path="rows.csv",
        content="name,age\nalice,30\nbob,25",
    ).execute({}, ctx)
    result = await _make_node(operation="parse_text", path="rows.csv").execute({}, ctx)
    assert result.success
    assert result.output_data["format"] == "csv"
    assert result.output_data["parsed"] == [
        {"name": "alice", "age": "30"},
        {"name": "bob", "age": "25"},
    ]


@pytest.mark.anyio
async def test_parse_text_auto_detects_json_by_content() -> None:
    """No extension — detection must fall back to content sniffing so
    downstream `code` nodes writing `output.dat` files still parse.
    """
    ctx = _make_ctx("pt3")
    await _make_node(operation="write", path="output.dat", content="[1,2,3]").execute({}, ctx)
    result = await _make_node(operation="parse_text", path="output.dat").execute({}, ctx)
    assert result.success
    assert result.output_data["format"] == "json"
    assert result.output_data["parsed"] == [1, 2, 3]


@pytest.mark.anyio
async def test_parse_text_missing_file_returns_error() -> None:
    ctx = _make_ctx("pt4")
    result = await _make_node(operation="parse_text", path="ghost.txt").execute({}, ctx)
    assert not result.success
    assert "File not found" in (result.error or "")


# ── read_url ─────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_read_url_size_cap_rejects_overflow() -> None:
    """A malicious/misconfigured URL that streams past the cap must
    fail loud, not silently truncate. Bounds are load-bearing — we
    can't OOM the worker on a giant PDF."""

    class _FakeStreamResponse:
        headers = {"content-type": "application/octet-stream"}
        status_code = 200

        def raise_for_status(self) -> None:
            pass

        async def aiter_bytes(self):
            yield b"x" * 200

    class _FakeStreamCtx:
        async def __aenter__(self):
            return _FakeStreamResponse()

        async def __aexit__(self, *a):
            return False

    client = MagicMock()
    client.stream = MagicMock(return_value=_FakeStreamCtx())
    ctx = NodeContext(
        execution_id="rd1",
        workflow_id="w",
        node_id="n",
        variables={},
        credentials=[],
        http_client=client,
    )
    node = _make_node(operation="read_url", url="http://x/big", max_bytes=100)
    result = await node.execute({}, ctx)
    assert not result.success
    assert "exceeded max_bytes" in (result.error or "")


@pytest.mark.anyio
async def test_read_url_returns_text_and_size() -> None:
    class _FakeStreamResponse:
        headers = {"content-type": "text/plain"}
        status_code = 200

        def raise_for_status(self) -> None:
            pass

        async def aiter_bytes(self):
            yield b"hello world"

    class _FakeStreamCtx:
        async def __aenter__(self):
            return _FakeStreamResponse()

        async def __aexit__(self, *a):
            return False

    client = MagicMock()
    client.stream = MagicMock(return_value=_FakeStreamCtx())
    ctx = NodeContext(
        execution_id="rd2",
        workflow_id="w",
        node_id="n",
        variables={},
        credentials=[],
        http_client=client,
    )
    node = _make_node(operation="read_url", url="http://x/hello")
    result = await node.execute({}, ctx)
    assert result.success
    assert result.output_data["content"] == "hello world"
    assert result.output_data["size_bytes"] == 11
    assert result.output_data["content_type"] == "text/plain"


# ── execution isolation ──────────────────────────────────────────────


def test_execution_roots_isolate_by_execution_id() -> None:
    """A file written under exec A must not be visible from exec B —
    otherwise a poisoned filename ("../../shared") could leak state
    across concurrent runs."""
    a = _execution_root("exec-a")
    b = _execution_root("exec-b")
    assert a != b
    (a / "x.txt").write_text("secret")
    assert not (b / "x.txt").exists()


def test_execution_id_sanitized() -> None:
    """Malicious execution_id like `../../root` must not break out of
    the temp dir prefix."""
    p = _execution_root("../../../etc")
    assert "rmc-exec-" in p.name
    # The sanitizer replaces every unsafe char, so the resulting name
    # cannot escape the tempdir parent.
    assert p.parent == Path(tempfile.gettempdir())
