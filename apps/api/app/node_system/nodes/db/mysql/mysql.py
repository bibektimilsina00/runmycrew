from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class MySQLProperties(BaseModel):
    connectionString: str = ""
    operation: str = "query"
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
            color="#1c1c1c",
            properties=[
                {
                    "name": "connectionString",
                    "label": "Connection String",
                    "type": "string",
                    "required": True,
                    "placeholder": "mysql://user:pass@host:3306/dbname",
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

    def _parse_dsn(self) -> dict[str, Any]:
        url = self.props.connectionString.strip()
        parsed = urlparse(url)
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 3306,
            "user": parsed.username or "root",
            "password": parsed.password or "",
            "db": parsed.path.lstrip("/") if parsed.path else "",
        }

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.connectionString.strip():
            return NodeResult(success=False, error="connectionString is required")
        if not self.props.sql.strip():
            return NodeResult(success=False, error="SQL is required")

        try:
            import aiomysql
        except ImportError:
            return NodeResult(
                success=False, error="aiomysql not installed. Run: pip install aiomysql"
            )

        params = self._parse_params()
        dsn = self._parse_dsn()
        try:
            conn = await aiomysql.connect(**dsn)
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
