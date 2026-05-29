from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import textwrap
from typing import Any

from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

# ── Sandbox (phase-A hardening) ───────────────────────────────────────────────
# User code runs in a separate process with a clean environment and OS resource
# limits. This means it cannot read the worker's in-memory secrets / DB handles
# or its environment variables, and cannot exhaust CPU, memory, or disk. It is
# defense-in-depth, NOT a full capability sandbox: the child can still reach the
# network and filesystem. True isolation (no net/fs) requires running each node
# in a locked-down container — that is the next phase.
_MEM_LIMIT_BYTES = 512 * 1024 * 1024
_FSIZE_LIMIT_BYTES = 16 * 1024 * 1024


def _sandbox_env() -> dict[str, str]:
    """Minimal environment for sandboxed code — deliberately omits the worker's secrets."""
    return {"PATH": "/usr/bin:/bin", "HOME": "/tmp", "LANG": "C.UTF-8"}


def _resource_limits(cpu_seconds: int):
    """Return a preexec_fn that caps CPU/file-size (and memory on Linux). POSIX only."""
    if os.name != "posix":
        return None

    def _apply() -> None:
        import resource
        from contextlib import suppress

        with suppress(ValueError, OSError):
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds + 1, cpu_seconds + 1))
        with suppress(ValueError, OSError):
            resource.setrlimit(resource.RLIMIT_FSIZE, (_FSIZE_LIMIT_BYTES, _FSIZE_LIMIT_BYTES))
        # RLIMIT_AS is unreliable on macOS; only enforce a hard memory cap on Linux.
        if sys.platform == "linux":
            with suppress(ValueError, OSError):
                resource.setrlimit(resource.RLIMIT_AS, (_MEM_LIMIT_BYTES, _MEM_LIMIT_BYTES))

    return _apply


async def _run_sandboxed(
    argv: list[str], stdin_bytes: bytes | None, timeout: int
) -> tuple[bytes, bytes, int]:
    """Run argv in a hardened child process (clean env + rlimits + hard timeout+kill)."""
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=_sandbox_env(),
        preexec_fn=_resource_limits(timeout),
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(stdin_bytes), timeout=timeout)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        raise TimeoutError(f"Code execution timed out after {timeout}s") from None
    return stdout_b, stderr_b, proc.returncode or 0


# Fixed bootstrap (no user interpolation → no quoting/format hazards). Reads
# {"code", "input"} from stdin, execs the user code with the documented globals,
# and writes {"output", "logs"} to stdout. User stdout/stderr are captured as logs.
_PY_BOOTSTRAP = r"""
import sys, json, io, math, re, datetime, collections
from contextlib import redirect_stdout, redirect_stderr

_payload = json.loads(sys.stdin.read())
_ns = {
    "__builtins__": __builtins__,
    "input": _payload.get("input", {}),
    "output": {},
    "logs": [],
    "json": json, "math": math, "re": re,
    "datetime": datetime, "collections": collections,
}
_out, _err = io.StringIO(), io.StringIO()
try:
    with redirect_stdout(_out), redirect_stderr(_err):
        exec(compile(_payload.get("code", ""), "<user-code>", "exec"), _ns)
except Exception as exc:
    sys.stderr.write(repr(exc))
    sys.exit(1)

_output = _ns.get("output", {})
if not isinstance(_output, dict):
    _output = {"result": _output}
_logs = [str(x) for x in _ns.get("logs", [])]
for _chunk in (_out.getvalue(), _err.getvalue()):
    _logs.extend(line for line in _chunk.strip().splitlines() if line)
sys.stdout.write(json.dumps({"output": _output, "logs": _logs}))
"""

_JS_WRAPPER = """\
const input = {input_json};
let output = {{}};
const logs = [];
const console = {{ log: (...a) => logs.push(a.map(String).join(' ')), error: (...a) => logs.push(a.map(String).join(' ')) }};
{code}
process.stdout.write(JSON.stringify({{ output, logs }}));
"""


class CodeProperties(BaseModel):
    language: str = "python"
    code: str = ""
    timeout: int = 30


class CodeNode(BaseNode[CodeProperties]):
    @classmethod
    def get_properties_model(cls) -> type[CodeProperties]:
        return CodeProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="logic.code",
            name="Code",
            category="logic",
            description="Run Python or JavaScript code. Access input data via `input`, set `output` to return data.",
            icon="Code2",
            color="#f59e0b",
            properties=[
                {
                    "name": "language",
                    "label": "Language",
                    "type": "options",
                    "default": "python",
                    "options": [
                        {"label": "Python", "value": "python"},
                        {"label": "JavaScript", "value": "javascript"},
                    ],
                },
                {
                    "name": "code",
                    "label": "Code",
                    "type": "code",
                    "required": True,
                    "default": "# Access previous node data via `input`\n# Set `output` to pass data to the next node\noutput = {'result': input}",
                    "description": "Python: set `output` dict. Use `{{node.output.field}}` to reference previous nodes.",
                    "condition": {"field": "language", "value": "python"},
                },
                {
                    "name": "code",
                    "label": "Code",
                    "type": "code",
                    "required": True,
                    "default": "// Access previous node data via `input`\n// Set `output` to pass data to the next node\noutput = { result: input };",
                    "description": "JavaScript: set `output` object. Use {{node.output.field}} to reference previous nodes.",
                    "condition": {"field": "language", "value": "javascript"},
                },
                {
                    "name": "timeout",
                    "label": "Timeout (seconds)",
                    "type": "number",
                    "default": 30,
                    "mode": "advanced",
                    "description": "Maximum execution time. Default 30s.",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "output", "type": "object"},
                {"label": "logs", "type": "array"},
                {"label": "language", "type": "string"},
            ],
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.code.strip():
            return NodeResult(success=False, error="Code is required.")

        timeout = max(1, min(self.props.timeout, 120))

        try:
            if self.props.language == "python":
                output, logs = await self._run_python(input_data, timeout)
            elif self.props.language == "javascript":
                output, logs = await self._run_javascript(input_data, timeout)
            else:
                return NodeResult(
                    success=False, error=f"Unsupported language: {self.props.language}"
                )
        except TimeoutError as e:
            return NodeResult(success=False, error=str(e))
        except Exception as e:
            return NodeResult(success=False, error=str(e))

        return NodeResult(
            success=True,
            output_data={
                "output": output,
                "logs": logs,
                "language": self.props.language,
                **output,  # spread output fields so downstream can reference them directly
            },
        )

    # ── Python ──────────────────────────────────────────────────────────────

    async def _run_python(
        self, input_data: dict[str, Any], timeout: int
    ) -> tuple[dict[str, Any], list[str]]:
        payload = json.dumps(
            {"code": textwrap.dedent(self.props.code), "input": input_data}
        ).encode("utf-8")
        # -I = isolated mode (ignore PYTHONPATH / user site / env-driven config).
        stdout_b, stderr_b, code = await _run_sandboxed(
            [sys.executable, "-I", "-c", _PY_BOOTSTRAP], payload, timeout
        )
        if code != 0:
            raise RuntimeError(
                stderr_b.decode("utf-8", errors="replace").strip() or "Python execution failed"
            )
        return self._parse_output(stdout_b)

    # ── JavaScript ──────────────────────────────────────────────────────────

    async def _run_javascript(
        self, input_data: dict[str, Any], timeout: int
    ) -> tuple[dict[str, Any], list[str]]:
        node_bin = shutil.which("node")
        if not node_bin:
            raise RuntimeError("Node.js not found. Install Node.js to run JavaScript code.")

        script = _JS_WRAPPER.format(input_json=json.dumps(input_data), code=self.props.code)
        stdout_b, stderr_b, code = await _run_sandboxed([node_bin, "-e", script], None, timeout)
        if code != 0:
            raise RuntimeError(
                f"JavaScript error: {stderr_b.decode('utf-8', errors='replace').strip()}"
            )
        return self._parse_output(stdout_b)

    @staticmethod
    def _parse_output(stdout_b: bytes) -> tuple[dict[str, Any], list[str]]:
        raw = stdout_b.decode("utf-8", errors="replace").strip()
        try:
            result = json.loads(raw)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Unexpected code output (not JSON): {raw[:200]}") from e

        output = result.get("output", {})
        if not isinstance(output, dict):
            output = {"result": output}
        return output, result.get("logs", [])
