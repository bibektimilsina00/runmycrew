"""SSH action node — run a remote command via asyncssh.

Shares the `ssh_credentials` provider with the SFTP node — host, port,
user, password / private key, and a known-hosts policy. Returns
`stdout`, `stderr`, `exit_status`, and a boolean `ok` (exit == 0).

Security note: default `known_hosts_policy` is `strict`. Do NOT flip
to `ignore` in prod — MITM window.
"""

from __future__ import annotations

from typing import Any

import asyncssh
from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class SshProperties(BaseModel):
    command: str = ""
    timeout_seconds: int = 60


def _known_hosts_arg(policy: str) -> Any:
    if policy in ("accept_new", "ignore"):
        return None
    return ()


def _make_client_keys(cred: dict[str, Any]) -> list[Any] | None:
    pem = cred.get("private_key") or ""
    if not pem:
        return None
    return [asyncssh.import_private_key(pem, passphrase=cred.get("passphrase") or None)]


class SshNode(BaseNode[SshProperties]):
    @classmethod
    def get_properties_model(cls):
        return SshProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.ssh",
            name="SSH Command",
            category="integration",
            inputs=1,
            outputs=1,
            description="Execute a remote command over SSH (asyncssh).",
            icon="ssh",
            color="#ffffff",
            credential_type="ssh_credentials",
            properties=[
                {
                    "name": "command",
                    "label": "Command",
                    "type": "string",
                    "required": True,
                    "placeholder": "uname -a",
                },
                {
                    "name": "timeout_seconds",
                    "label": "Timeout (seconds)",
                    "type": "number",
                    "default": 60,
                },
            ],
            outputs_schema=[
                {"label": "ok", "type": "boolean"},
                {"label": "exit_status", "type": "number"},
                {"label": "stdout", "type": "string"},
                {"label": "stderr", "type": "string"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        cred = self.credential or {}
        host = cred.get("host") or ""
        if not host:
            return NodeResult(success=False, error="SSH credential missing host")
        p = self.props
        try:
            async with asyncssh.connect(
                host,
                port=int(cred.get("port") or 22),
                username=cred.get("username") or "",
                password=cred.get("password") or None,
                client_keys=_make_client_keys(cred),
                known_hosts=_known_hosts_arg(cred.get("known_hosts_policy") or "strict"),
            ) as conn:
                result = await conn.run(p.command or "", timeout=p.timeout_seconds)
                return NodeResult(
                    success=True,
                    output_data={
                        "ok": (result.exit_status == 0),
                        "exit_status": result.exit_status,
                        "stdout": result.stdout or "",
                        "stderr": result.stderr or "",
                    },
                )
        except (asyncssh.Error, OSError, TimeoutError) as e:
            return NodeResult(success=False, error=f"SSH failed: {e}")
