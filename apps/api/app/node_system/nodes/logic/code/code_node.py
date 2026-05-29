from __future__ import annotations

import asyncio
import io
import json
import textwrap
from contextlib import redirect_stderr, redirect_stdout
from typing import Any

from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

_PYTHON_TEMPLATE = """\
import json, math, re, datetime, collections
from typing import Any

input = __input__
output = {{}}
logs = []

{code}
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
                output, logs = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, self._run_python, input_data),
                    timeout=timeout,
                )
            elif self.props.language == "javascript":
                output, logs = await asyncio.wait_for(
                    self._run_javascript(input_data),
                    timeout=timeout,
                )
            else:
                return NodeResult(
                    success=False, error=f"Unsupported language: {self.props.language}"
                )
        except TimeoutError:
            return NodeResult(success=False, error=f"Code execution timed out after {timeout}s.")
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

    def _run_python(self, input_data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        code = textwrap.dedent(self.props.code)
        namespace: dict[str, Any] = {
            "__builtins__": __import__("builtins"),
            "__input__": input_data,
        }
        full_code = _PYTHON_TEMPLATE.format(code=code)

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            exec(full_code, namespace)  # noqa: S102

        output = namespace.get("output", {})
        if not isinstance(output, dict):
            output = {"result": output}

        logs = []
        raw_logs = namespace.get("logs", [])
        if isinstance(raw_logs, list):
            logs.extend(str(line) for line in raw_logs)
        stdout_text = stdout_buf.getvalue().strip()
        stderr_text = stderr_buf.getvalue().strip()
        if stdout_text:
            logs.extend(stdout_text.splitlines())
        if stderr_text:
            logs.extend(stderr_text.splitlines())

        return output, logs

    # ── JavaScript ──────────────────────────────────────────────────────────

    async def _run_javascript(self, input_data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        import shutil

        node_bin = shutil.which("node")
        if not node_bin:
            raise RuntimeError("Node.js not found. Install Node.js to run JavaScript code.")

        script = _JS_WRAPPER.format(
            input_json=json.dumps(input_data),
            code=self.props.code,
        )

        proc = await asyncio.create_subprocess_exec(
            node_bin,
            "-e",
            script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()

        if proc.returncode != 0:
            err = stderr_bytes.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"JavaScript error: {err}")

        raw = stdout_bytes.decode("utf-8", errors="replace").strip()
        try:
            result = json.loads(raw)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Unexpected JS output (not JSON): {raw[:200]}") from e

        output = result.get("output", {})
        if not isinstance(output, dict):
            output = {"result": output}
        logs = result.get("logs", [])
        return output, logs
