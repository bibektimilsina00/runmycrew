from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class Neo4jProperties(BaseModel):
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = ""
    database: str = "neo4j"
    query: str = ""  # Cypher query
    params: Any = None  # Query parameters dict


class Neo4jNode(BaseNode[Neo4jProperties]):
    @classmethod
    def get_properties_model(cls) -> type[Neo4jProperties]:
        return Neo4jProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.neo4j",
            name="Neo4j",
            category="integration",
            description="Run a Cypher query against a Neo4j graph database.",
            icon="neo4j",
            color="#1c1c1c",
            properties=[
                {
                    "name": "uri",
                    "label": "URI",
                    "type": "string",
                    "default": "bolt://localhost:7687",
                },
                {"name": "username", "label": "Username", "type": "string", "default": "neo4j"},
                {"name": "password", "label": "Password", "type": "string", "required": True},
                {"name": "database", "label": "Database", "type": "string", "default": "neo4j"},
                {
                    "name": "query",
                    "label": "Cypher Query",
                    "type": "string",
                    "required": True,
                    "placeholder": "MATCH (n:Person {name: $name}) RETURN n",
                },
                {
                    "name": "params",
                    "label": "Parameters",
                    "type": "json",
                    "default": {},
                    "mode": "advanced",
                    "description": "Dict of named parameters for the Cypher query.",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "records", "type": "array"},
                {"label": "count", "type": "number"},
            ],
            allow_error=True,
        )

    def _parse_params(self) -> dict[str, Any]:
        raw = self.props.params
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                return {}
        return raw if isinstance(raw, dict) else {}

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.query.strip():
            return NodeResult(success=False, error="query is required")
        if not self.props.password.strip():
            return NodeResult(success=False, error="password is required")

        try:
            from neo4j import AsyncGraphDatabase  # type: ignore[import]
        except ImportError:
            return NodeResult(success=False, error="neo4j not installed. Run: pip install neo4j")

        params = self._parse_params()
        driver = AsyncGraphDatabase.driver(
            self.props.uri,
            auth=(self.props.username, self.props.password),
        )
        try:
            async with driver.session(database=self.props.database) as session:
                result = await session.run(self.props.query, params)
                records = [dict(r) for r in await result.data()]
                return NodeResult(
                    success=True,
                    output_data={"records": records, "count": len(records)},
                )
        except Exception as e:
            return NodeResult(success=False, error=f"Neo4j error: {e}")
        finally:
            await driver.close()
