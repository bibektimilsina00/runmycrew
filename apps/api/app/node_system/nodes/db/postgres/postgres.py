from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class PostgresProperties(BaseModel):
    credential: str = ""
    connectionString: str = ""
    operation: str = "query"  # query | execute
    schema: str = "public"
    table: str = ""
    sql: str = ""
    params: Any = Field(default_factory=list)


class PostgresNode(BaseNode[PostgresProperties]):
    @classmethod
    def get_properties_model(cls) -> type[PostgresProperties]:
        return PostgresProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.postgres",
            name="PostgreSQL",
            category="integration",
            description="Query or execute SQL against a PostgreSQL database.",
            icon="postgresql",
            color="#ffffff",
            properties=[
                {
                    "name": "credential",
                    "label": "Postgres Account",
                    "type": "credential",
                    "credentialType": "postgres_credentials",
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "query",
                    "options": [
                        {"label": "Query (SELECT)", "value": "query"},
                        {"label": "Execute (INSERT/UPDATE/DELETE)", "value": "execute"},
                    ],
                },
                {
                    "name": "schema",
                    "label": "Schema",
                    "type": "string",
                    "default": "public",
                    "mode": "advanced",
                    "remote": {
                        "provider": "postgres",
                        "resource": "schemas",
                        "params": {},
                        "depends_on": [],
                        "allow_manual": True,
                    },
                },
                {
                    "name": "table",
                    "label": "Table",
                    "type": "string",
                    "mode": "advanced",
                    "remote": {
                        "provider": "postgres",
                        "resource": "tables",
                        "params": {"schema": "${schema}"},
                        "depends_on": ["schema"],
                        "allow_manual": True,
                    },
                },
                {
                    "name": "sql",
                    "label": "SQL",
                    "type": "string",
                    "required": True,
                    "placeholder": "SELECT * FROM users WHERE id = $1",
                },
                {
                    "name": "params",
                    "label": "Parameters",
                    "type": "json",
                    "default": [],
                    "mode": "advanced",
                    "description": "Array of parameter values for $1, $2, ... placeholders.",
                },
                {
                    "name": "connectionString",
                    "label": "Connection String (legacy)",
                    "type": "string",
                    "mode": "advanced",
                    "placeholder": "postgresql://user:pass@host:5432/dbname",
                    "description": "Direct connection string. Use only if not using a credential.",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "rows", "type": "array"},
                {"label": "rowCount", "type": "number"},
            ],
            allow_error=True,
        )

    def _parse_params(self) -> list[Any]:
        raw = self.props.params
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                return []
        return raw if isinstance(raw, list) else []

    async def _resolve_connect_kwargs(self, context: NodeContext) -> dict[str, Any]:
        """Return asyncpg connect() kwargs.

        Prefers the workspace credential the picker uses. Falls back to
        the legacy inline connectionString so old workflows keep
        working during migration."""
        cred_id = (self.props.credential or "").strip()
        if cred_id:
            from apps.api.app.core.database import AsyncSessionLocal
            from apps.api.app.features.credentials.service import CredentialService

            async with AsyncSessionLocal() as db:
                service = CredentialService(db)
                import uuid as _uuid

                cred_row = await service.repo.get_by_id_and_workspace(
                    _uuid.UUID(cred_id), context.workspace_id
                )
                if cred_row is None:
                    raise ValueError("Postgres credential not found for this workspace.")
                data = await service.get_decrypted_credential(cred_row)
            if not isinstance(data, dict):
                raise ValueError("Postgres credential has no decrypted data.")
            if dsn := data.get("connectionString") or data.get("dsn"):
                return {"dsn": dsn}
            kwargs: dict[str, Any] = {}
            for k in ("host", "port", "user", "password", "database"):
                if v := data.get(k):
                    kwargs[k] = int(v) if k == "port" and isinstance(v, str) else v
            if not kwargs:
                raise ValueError("Postgres credential missing host or connectionString.")
            return kwargs
        if self.props.connectionString.strip():
            return {"dsn": self.props.connectionString}
        raise ValueError("Select a credential or paste a connection string.")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.sql.strip():
            return NodeResult(success=False, error="SQL is required")

        try:
            import asyncpg
        except ImportError:
            return NodeResult(
                success=False, error="asyncpg not installed. Run: pip install asyncpg"
            )

        try:
            connect_kwargs = await self._resolve_connect_kwargs(context)
        except ValueError as e:
            return NodeResult(success=False, error=str(e))

        params = self._parse_params()
        try:
            conn = await asyncpg.connect(**connect_kwargs)
            try:
                if self.props.operation == "query":
                    records = await conn.fetch(self.props.sql, *params)
                    rows = [dict(r) for r in records]
                    return NodeResult(
                        success=True, output_data={"rows": rows, "rowCount": len(rows)}
                    )
                else:
                    status = await conn.execute(self.props.sql, *params)
                    # status format: "INSERT 0 5" or "UPDATE 3"
                    parts = status.split()
                    count = int(parts[-1]) if parts and parts[-1].isdigit() else 0
                    return NodeResult(
                        success=True, output_data={"rows": [], "rowCount": count, "status": status}
                    )
            finally:
                await conn.close()
        except Exception as e:
            return NodeResult(success=False, error=f"PostgreSQL error: {e}")
