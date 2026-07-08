"""PostgreSQL action node — run parameterized SQL against a Postgres DB.

Uses `asyncpg` directly (already a dependency of the API for its own
data store). Not a REST scaffold — this speaks native pg wire.

Ops:
  - `query`   — SELECT-style, returns list of rows (fetch)
  - `execute` — INSERT/UPDATE/DELETE, returns affected row count
  - `execute_many` — batch insert with a list of parameter tuples

Parameters use `$1, $2, ...` placeholders (asyncpg's native form). We
never string-interpolate user input into SQL — anything that varies
per call MUST come through `params`. Credential holds host/port/user/
password/database/ssl.
"""

from __future__ import annotations

from typing import Any

import asyncpg
from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class PostgresqlProperties(BaseModel):
    operation: str = "query"
    sql: str = ""
    params: list[Any] = []
    param_batches: list[list[Any]] = []


class PostgresqlNode(BaseNode[PostgresqlProperties]):
    @classmethod
    def get_properties_model(cls):
        return PostgresqlProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.postgresql",
            name="PostgreSQL",
            category="integration",
            inputs=1,
            outputs=1,
            description="Run parameterized SQL against a PostgreSQL database.",
            icon="postgresql",
            color="#ffffff",
            credential_type="postgresql_credentials",
            properties=[
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "query",
                    "options": [
                        {"label": "Query (SELECT)", "value": "query"},
                        {"label": "Execute (INSERT / UPDATE / DELETE)", "value": "execute"},
                        {"label": "Execute Many (batch)", "value": "execute_many"},
                    ],
                },
                {
                    "name": "sql",
                    "label": "SQL",
                    "type": "code",
                    "required": True,
                    "placeholder": "SELECT id, email FROM users WHERE created_at > $1",
                },
                {
                    "name": "params",
                    "label": "Params (JSON array — $1, $2, ...)",
                    "type": "json",
                    "default": [],
                    "condition": {"field": "operation", "value": ["query", "execute"]},
                },
                {
                    "name": "param_batches",
                    "label": "Batches (JSON — array of param arrays)",
                    "type": "json",
                    "default": [],
                    "condition": {"field": "operation", "value": ["execute_many"]},
                },
            ],
            outputs_schema=[
                {"label": "rows", "type": "array"},
                {"label": "row_count", "type": "number"},
                {"label": "operation", "type": "string"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        cred = self.credential or {}
        if not cred.get("host"):
            return NodeResult(success=False, error="Postgres credential missing host")
        dsn_kwargs = {
            "host": cred.get("host"),
            "port": int(cred.get("port") or 5432),
            "user": cred.get("user") or "",
            "password": cred.get("password") or "",
            "database": cred.get("database") or "",
        }
        ssl = cred.get("ssl") or "prefer"
        if ssl == "require":
            dsn_kwargs["ssl"] = True
        elif ssl == "disable":
            dsn_kwargs["ssl"] = False
        # `prefer` = asyncpg default (negotiates)

        p = self.props
        try:
            conn = await asyncpg.connect(**dsn_kwargs, timeout=30)
        except (asyncpg.PostgresError, OSError, TimeoutError) as e:
            return NodeResult(success=False, error=f"Postgres connect failed: {e}")

        try:
            if p.operation == "query":
                records = await conn.fetch(p.sql or "", *(p.params or []))
                rows = [dict(r) for r in records]
                return NodeResult(
                    success=True,
                    output_data={
                        "operation": "query",
                        "rows": rows,
                        "row_count": len(rows),
                    },
                )
            if p.operation == "execute":
                # asyncpg's execute returns a status string like "INSERT 0 1".
                status = await conn.execute(p.sql or "", *(p.params or []))
                # Parse row count from status string tail.
                affected = 0
                parts = (status or "").split()
                if parts and parts[-1].isdigit():
                    affected = int(parts[-1])
                return NodeResult(
                    success=True,
                    output_data={
                        "operation": "execute",
                        "row_count": affected,
                        "status": status or "",
                    },
                )
            if p.operation == "execute_many":
                await conn.executemany(p.sql or "", p.param_batches or [])
                return NodeResult(
                    success=True,
                    output_data={
                        "operation": "execute_many",
                        "row_count": len(p.param_batches or []),
                    },
                )
            return NodeResult(success=False, error=f"Unknown operation: {p.operation}")
        except asyncpg.PostgresError as e:
            return NodeResult(success=False, error=f"Postgres error: {e}")
        finally:
            await conn.close()
