from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class PostgresProperties(BaseModel):
    connectionString: str = ""
    operation: str = "query"  # query | execute
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
            icon="Database",
            color="#336791",
            properties=[
                {
                    "name": "connectionString",
                    "label": "Connection String",
                    "type": "string",
                    "required": True,
                    "placeholder": "postgresql://user:pass@host:5432/dbname",
                    "description": "PostgreSQL connection string.",
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

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.connectionString.strip():
            return NodeResult(success=False, error="connectionString is required")
        if not self.props.sql.strip():
            return NodeResult(success=False, error="SQL is required")

        try:
            import asyncpg
        except ImportError:
            return NodeResult(success=False, error="asyncpg not installed. Run: pip install asyncpg")

        params = self._parse_params()
        try:
            conn = await asyncpg.connect(self.props.connectionString)
            try:
                if self.props.operation == "query":
                    records = await conn.fetch(self.props.sql, *params)
                    rows = [dict(r) for r in records]
                    return NodeResult(success=True, output_data={"rows": rows, "rowCount": len(rows)})
                else:
                    status = await conn.execute(self.props.sql, *params)
                    # status format: "INSERT 0 5" or "UPDATE 3"
                    parts = status.split()
                    count = int(parts[-1]) if parts and parts[-1].isdigit() else 0
                    return NodeResult(success=True, output_data={"rows": [], "rowCount": count, "status": status})
            finally:
                await conn.close()
        except Exception as e:
            return NodeResult(success=False, error=f"PostgreSQL error: {e}")
