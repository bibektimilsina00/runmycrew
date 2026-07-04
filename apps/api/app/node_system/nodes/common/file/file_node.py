"""File node — read from URL / write / append / parse text files.

Sim-parity for the "file" core block. Four operations:

  - `read_url`: fetch a URL, return text + bytes size + content-type
  - `write`: save inline content to a per-execution temp path, return
    the path for downstream nodes to consume
  - `append`: append inline content to an existing per-execution file
  - `parse_text`: pass-through parser for common text formats
    (JSON, CSV, plain text) — auto-detects by extension or by sniffing
    the first few bytes

Persistence model: files live under `/tmp/rmc-exec-{execution_id}/` for
the lifetime of the workflow execution. Not a durable workspace store —
just enough to hand a file between two nodes on the same run. A future
Deployments/Storage block will bring real workspace file persistence.
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)


class FileProperties(BaseModel):
    operation: str = "read_url"
    # read_url
    url: str | None = None
    max_bytes: int = 10 * 1024 * 1024  # 10 MiB — bound download size
    # write / append
    path: str | None = None  # relative to per-execution root; must not escape
    content: str | None = None
    encoding: str = "utf-8"
    # parse_text
    format: str | None = None  # "json", "csv", "text", or None = auto


def _execution_root(execution_id: str) -> Path:
    """Per-execution scratch dir under system temp. Isolates one
    workflow run from another so a downstream node reading `path` can't
    accidentally hit another workflow's writes."""
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", execution_id or "unknown")
    root = Path(tempfile.gettempdir()) / f"rmc-exec-{safe}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_path(root: Path, user_path: str) -> Path:
    """Resolve `user_path` under `root`, refusing traversal (`../`,
    absolute paths). Prevents a malicious workflow from writing under
    `/etc/` or reading arbitrary files."""
    if not user_path:
        raise ValueError("path is required")
    p = (root / user_path).resolve()
    root_resolved = root.resolve()
    if not str(p).startswith(str(root_resolved) + os.sep) and p != root_resolved:
        raise ValueError(f"path escapes execution root: {user_path!r}")
    return p


def _detect_format(name: str, sample: str) -> str:
    """Heuristic format detection when `format` prop is None."""
    lower = (name or "").lower()
    if lower.endswith(".json"):
        return "json"
    if lower.endswith((".csv", ".tsv")):
        return "csv"
    stripped = sample.lstrip()
    if stripped.startswith(("{", "[")):
        return "json"
    return "text"


class FileNode(BaseNode[FileProperties]):
    @classmethod
    def get_properties_model(cls) -> type[FileProperties]:
        return FileProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="common.file",
            name="File",
            category="logic",
            description=(
                "Read a URL, write / append text to a per-execution file, or "
                "parse a text file (JSON / CSV / plain text)."
            ),
            icon="File",
            color="#f59e0b",
            properties=[
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "read_url",
                    "options": [
                        {"label": "Read from URL", "value": "read_url"},
                        {"label": "Write file", "value": "write"},
                        {"label": "Append to file", "value": "append"},
                        {"label": "Parse text file", "value": "parse_text"},
                    ],
                },
                {
                    "name": "url",
                    "label": "URL",
                    "type": "string",
                    "required": True,
                    "condition": {"field": "operation", "value": "read_url"},
                },
                {
                    "name": "max_bytes",
                    "label": "Max download bytes",
                    "type": "number",
                    "default": 10 * 1024 * 1024,
                    "mode": "advanced",
                    "condition": {"field": "operation", "value": "read_url"},
                },
                {
                    "name": "path",
                    "label": "Path (relative to execution root)",
                    "type": "string",
                    "required": True,
                    "condition": {
                        "field": "operation",
                        "value": ["write", "append", "parse_text"],
                    },
                    "placeholder": "output.json",
                },
                {
                    "name": "content",
                    "label": "Content",
                    "type": "string",
                    "required": True,
                    "condition": {"field": "operation", "value": ["write", "append"]},
                },
                {
                    "name": "encoding",
                    "label": "Encoding",
                    "type": "string",
                    "default": "utf-8",
                    "mode": "advanced",
                    "condition": {
                        "field": "operation",
                        "value": ["write", "append", "parse_text", "read_url"],
                    },
                },
                {
                    "name": "format",
                    "label": "Format (blank = auto-detect)",
                    "type": "options",
                    "default": None,
                    "mode": "advanced",
                    "options": [
                        {"label": "Auto-detect", "value": ""},
                        {"label": "JSON", "value": "json"},
                        {"label": "CSV", "value": "csv"},
                        {"label": "Plain text", "value": "text"},
                    ],
                    "condition": {"field": "operation", "value": "parse_text"},
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "operation", "type": "string"},
                {"label": "path", "type": "string"},
                {"label": "url", "type": "string"},
                {"label": "content", "type": "string"},
                {"label": "size_bytes", "type": "number"},
                {"label": "content_type", "type": "string"},
                {"label": "parsed", "type": "object"},
                {"label": "format", "type": "string"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:  # noqa: ARG002
        op = self.props.operation
        if op == "read_url":
            return await self._read_url(context)
        if op == "write":
            return await self._write(context, append=False)
        if op == "append":
            return await self._write(context, append=True)
        if op == "parse_text":
            return await self._parse_text(context)
        return NodeResult(success=False, error=f"Unknown operation {op!r}")

    async def _read_url(self, context: NodeContext) -> NodeResult:
        url = (self.props.url or "").strip()
        if not url:
            return NodeResult(success=False, error="url is required")
        try:
            max_bytes = max(1, int(self.props.max_bytes or 10 * 1024 * 1024))
        except (TypeError, ValueError):
            max_bytes = 10 * 1024 * 1024
        try:
            client: httpx.AsyncClient = context.http_client
            # Stream so we can bail early if the response exceeds the
            # cap — some upstream URLs will happily hand us a 1 GiB
            # file if we let them.
            async with client.stream("GET", url, timeout=30, follow_redirects=True) as resp:
                resp.raise_for_status()
                chunks: list[bytes] = []
                total = 0
                async for chunk in resp.aiter_bytes():
                    total += len(chunk)
                    if total > max_bytes:
                        return NodeResult(
                            success=False,
                            error=f"Response exceeded max_bytes ({max_bytes}); got at least {total}.",
                        )
                    chunks.append(chunk)
                body = b"".join(chunks)
                content_type = resp.headers.get("content-type", "")
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=f"HTTP {exc.response.status_code}: {exc.response.text[:200]}",
            )
        except Exception as exc:  # noqa: BLE001
            return NodeResult(success=False, error=f"URL fetch failed: {exc}")

        encoding = self.props.encoding or "utf-8"
        try:
            text = body.decode(encoding, errors="replace")
        except LookupError:
            text = body.decode("utf-8", errors="replace")
        return NodeResult(
            success=True,
            output_data={
                "operation": "read_url",
                "url": url,
                "content": text,
                "size_bytes": total,
                "content_type": content_type,
            },
        )

    async def _write(self, context: NodeContext, *, append: bool) -> NodeResult:
        try:
            root = _execution_root(context.execution_id)
            path = _safe_path(root, self.props.path or "")
        except ValueError as exc:
            return NodeResult(success=False, error=str(exc))
        content = self.props.content or ""
        encoding = self.props.encoding or "utf-8"
        mode = "a" if append else "w"
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open(mode, encoding=encoding) as f:
                f.write(content)
        except OSError as exc:
            return NodeResult(success=False, error=f"File write failed: {exc}")
        size = 0
        with contextlib.suppress(OSError):
            size = path.stat().st_size
        return NodeResult(
            success=True,
            output_data={
                "operation": "append" if append else "write",
                "path": str(path),
                "size_bytes": size,
            },
        )

    async def _parse_text(self, context: NodeContext) -> NodeResult:
        try:
            root = _execution_root(context.execution_id)
            path = _safe_path(root, self.props.path or "")
        except ValueError as exc:
            return NodeResult(success=False, error=str(exc))
        if not path.exists():
            return NodeResult(success=False, error=f"File not found: {path}")
        encoding = self.props.encoding or "utf-8"
        try:
            raw = path.read_text(encoding=encoding, errors="replace")
        except OSError as exc:
            return NodeResult(success=False, error=f"File read failed: {exc}")

        fmt = (self.props.format or "").strip().lower() or _detect_format(str(path), raw[:1024])
        parsed: Any = None
        if fmt == "json":
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                return NodeResult(success=False, error=f"JSON parse failed: {exc}")
        elif fmt == "csv":
            try:
                reader = csv.DictReader(io.StringIO(raw))
                parsed = list(reader)
            except csv.Error as exc:
                return NodeResult(success=False, error=f"CSV parse failed: {exc}")
        else:
            parsed = raw

        return NodeResult(
            success=True,
            output_data={
                "operation": "parse_text",
                "path": str(path),
                "content": raw,
                "size_bytes": len(raw.encode(encoding, errors="replace")),
                "parsed": parsed,
                "format": fmt,
            },
        )
