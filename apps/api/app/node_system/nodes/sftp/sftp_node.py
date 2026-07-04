"""SFTP action node — file transfer + directory ops over SSH.

Uses `asyncssh`. Credential holds host, port, username, and either
password or a PEM private key. `known_hosts_policy` is `strict` by
default (RECOMMENDED); dev deployments can set it to `accept_new` or
`ignore` on the credential.

Ops:
  - list_dir: return names + sizes in a remote directory
  - read_file: fetch a remote file into `content` (utf-8 or base64)
  - write_file: upload a string as a remote file
  - delete_file: remove a remote file
  - move_file: rename / move a remote file
  - mkdir: create a remote directory
  - stat: stat a remote path
"""

from __future__ import annotations

import base64
from typing import Any

import asyncssh
from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class SftpProperties(BaseModel):
    operation: str = "list_dir"
    path: str = "."
    dest_path: str | None = None
    content: str | None = None
    encoding: str = "utf-8"  # utf-8 | base64


def _known_hosts_arg(policy: str) -> Any:
    """asyncssh known_hosts kwarg:
    - `strict` (default) → use ~/.ssh/known_hosts
    - `accept_new` / `ignore` → None (host key check disabled)"""
    if policy in ("accept_new", "ignore"):
        return None
    return ()


def _make_client_keys(cred: dict[str, Any]) -> list[Any] | None:
    pem = cred.get("private_key") or ""
    if not pem:
        return None
    return [asyncssh.import_private_key(pem, passphrase=cred.get("passphrase") or None)]


class SftpNode(BaseNode[SftpProperties]):
    @classmethod
    def get_properties_model(cls):
        return SftpProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.sftp",
            name="SFTP",
            category="integration",
            inputs=1,
            outputs=1,
            description="Transfer files + browse directories over SFTP (asyncssh).",
            icon="sftp",
            color="#1c1c1c",
            credential_type="ssh_credentials",
            properties=[
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "list_dir",
                    "options": [
                        {"label": "List Directory", "value": "list_dir"},
                        {"label": "Read File", "value": "read_file"},
                        {"label": "Write File", "value": "write_file"},
                        {"label": "Delete File", "value": "delete_file"},
                        {"label": "Move / Rename", "value": "move_file"},
                        {"label": "Make Directory", "value": "mkdir"},
                        {"label": "Stat", "value": "stat"},
                    ],
                },
                {"name": "path", "label": "Remote Path", "type": "string", "required": True},
                {
                    "name": "dest_path",
                    "label": "Destination (for move)",
                    "type": "string",
                    "condition": {"field": "operation", "value": ["move_file"]},
                },
                {
                    "name": "content",
                    "label": "Content (for write)",
                    "type": "string",
                    "condition": {"field": "operation", "value": ["write_file"]},
                },
                {
                    "name": "encoding",
                    "label": "Encoding",
                    "type": "options",
                    "default": "utf-8",
                    "options": [
                        {"label": "UTF-8 text", "value": "utf-8"},
                        {"label": "Base64 binary", "value": "base64"},
                    ],
                },
            ],
            outputs_schema=[
                {"label": "operation", "type": "string"},
                {"label": "path", "type": "string"},
                {"label": "entries", "type": "array"},
                {"label": "content", "type": "string"},
                {"label": "stat", "type": "object"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        cred = self.credential or {}
        host = cred.get("host") or ""
        if not host:
            return NodeResult(success=False, error="SSH credential missing host")
        port = int(cred.get("port") or 22)
        username = cred.get("username") or ""
        password = cred.get("password") or None
        known_hosts = _known_hosts_arg(cred.get("known_hosts_policy") or "strict")
        p = self.props

        try:
            async with (
                asyncssh.connect(
                    host,
                    port=port,
                    username=username,
                    password=password,
                    client_keys=_make_client_keys(cred),
                    known_hosts=known_hosts,
                ) as conn,
                conn.start_sftp_client() as sftp,
            ):
                output: dict[str, Any] = {"operation": p.operation, "path": p.path}
                if p.operation == "list_dir":
                    entries = []
                    for item in await sftp.readdir(p.path):
                        entries.append(
                            {
                                "name": item.filename,
                                "size": item.attrs.size,
                                "mtime": item.attrs.mtime,
                                "is_dir": bool(
                                    item.attrs.permissions and item.attrs.permissions & 0o040000
                                ),
                            }
                        )
                    output["entries"] = entries
                elif p.operation == "read_file":
                    async with sftp.open(p.path, "rb") as fh:
                        raw = await fh.read()
                    if p.encoding == "base64":
                        output["content"] = base64.b64encode(raw).decode("ascii")
                    else:
                        output["content"] = raw.decode("utf-8", errors="replace")
                    output["size"] = len(raw)
                elif p.operation == "write_file":
                    data = p.content or ""
                    raw = base64.b64decode(data) if p.encoding == "base64" else data.encode("utf-8")
                    async with sftp.open(p.path, "wb") as fh:
                        await fh.write(raw)
                    output["written"] = len(raw)
                elif p.operation == "delete_file":
                    await sftp.remove(p.path)
                    output["deleted"] = True
                elif p.operation == "move_file":
                    if not p.dest_path:
                        return NodeResult(success=False, error="dest_path required for move_file")
                    await sftp.rename(p.path, p.dest_path)
                    output["moved_to"] = p.dest_path
                elif p.operation == "mkdir":
                    await sftp.mkdir(p.path)
                    output["created"] = True
                elif p.operation == "stat":
                    attrs = await sftp.stat(p.path)
                    output["stat"] = {
                        "size": attrs.size,
                        "mtime": attrs.mtime,
                        "permissions": attrs.permissions,
                    }
                else:
                    return NodeResult(success=False, error=f"Unknown SFTP operation: {p.operation}")
                return NodeResult(success=True, output_data=output)
        except (asyncssh.Error, OSError) as e:
            return NodeResult(success=False, error=f"SFTP failed: {e}")
