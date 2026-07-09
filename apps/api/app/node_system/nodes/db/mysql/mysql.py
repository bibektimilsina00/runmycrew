from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.db._credential_resolver import resolve_credential


class MySQLProperties(BaseModel):
    credential: str = ""
    connectionString: str = ""
    operation: str = "query"
    schema: str = ""
    table: str = ""
    sql: str = ""
    params: Any = Field(default_factory=list)


class MySQLNode(BaseNode[MySQLProperties]):
    @classmethod
    def get_properties_model(cls) -> type[MySQLProperties]:
        return MySQLProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.mysql",
            name="MySQL",
            category="integration",
            description="Query or execute SQL against a MySQL database.",
            icon="mysql",
            color="#ffffff",
            properties=[
                {
                    "name": "credential",
                    "label": "MySQL Account",
                    "type": "credential",
                    "credentialType": "mysql_credentials",
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
                    "label": "Database / Schema",
                    "type": "string",
                    "mode": "advanced",
                    "remote": {
                        "provider": "mysql",
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
                        "provider": "mysql",
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
                    "placeholder": "SELECT * FROM users WHERE id = %s",
                },
                {
                    "name": "params",
                    "label": "Parameters",
                    "type": "json",
                    "default": [],
                    "mode": "advanced",
                    "description": "Array of parameter values for %s placeholders.",
                },
                {
                    "name": "connectionString",
                    "label": "Connection String (legacy)",
                    "type": "string",
                    "mode": "advanced",
                    "placeholder": "mysql://user:pass@host:3306/dbname",
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

    def _parse_dsn(self, url: str) -> dict[str, Any]:
        parsed = urlparse(url)
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 3306,
            "user": parsed.username or "root",
            "password": parsed.password or "",
            "db": parsed.path.lstrip("/") if parsed.path else "",
        }

    async def _resolve_connect_kwargs(self, context: NodeContext) -> dict[str, Any]:
        cred_id = (self.props.credential or "").strip()
        if cred_id:
            data = await resolve_credential(cred_id, context.workspace_id)
            if not data:
                raise ValueError("MySQL credential not found for this workspace.")
            if dsn := data.get("connectionString") or data.get("dsn"):
                return self._parse_dsn(dsn)
            kwargs: dict[str, Any] = {}
            for k in ("host", "port", "user", "password"):
                if v := data.get(k):
                    kwargs[k] = int(v) if k == "port" and isinstance(v, str) else v
            if db := data.get("database") or data.get("db"):
                kwargs["db"] = db
            if not kwargs.get("host"):
                raise ValueError("MySQL credential missing host or connectionString.")
            return kwargs
        if self.props.connectionString.strip():
            return self._parse_dsn(self.props.connectionString)
        raise ValueError("Select a credential or paste a connection string.")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.sql.strip():
            return NodeResult(success=False, error="SQL is required")

        try:
            import aiomysql
        except ImportError:
            return NodeResult(
                success=False, error="aiomysql not installed. Run: pip install aiomysql"
            )

        try:
            connect_kwargs = await self._resolve_connect_kwargs(context)
        except ValueError as e:
            return NodeResult(success=False, error=str(e))

        params = self._parse_params()
        try:
            conn = await aiomysql.connect(**connect_kwargs)
            try:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(self.props.sql, params or None)
                    if self.props.operation == "query":
                        rows = list(await cur.fetchall())
                        return NodeResult(
                            success=True, output_data={"rows": rows, "rowCount": len(rows)}
                        )
                    else:
                        await conn.commit()
                        return NodeResult(
                            success=True, output_data={"rows": [], "rowCount": cur.rowcount}
                        )
            finally:
                conn.close()
        except Exception as e:
            return NodeResult(success=False, error=f"MySQL error: {e}")
