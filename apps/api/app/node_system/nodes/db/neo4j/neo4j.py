from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.db._credential_resolver import resolve_credential


class Neo4jProperties(BaseModel):
    credential: str = ""
    uri: str = ""
    username: str = ""
    password: str = ""
    database: str = "neo4j"
    label: str = ""
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
            color="#ffffff",
            properties=[
                {
                    "name": "credential",
                    "label": "Neo4j Account",
                    "type": "credential",
                    "credentialType": "neo4j_credentials",
                    "required": True,
                },
                {
                    "name": "database",
                    "label": "Database",
                    "type": "string",
                    "default": "neo4j",
                    "remote": {
                        "provider": "neo4j",
                        "resource": "databases",
                        "params": {},
                        "depends_on": [],
                        "allow_manual": True,
                    },
                },
                {
                    "name": "label",
                    "label": "Node Label",
                    "type": "string",
                    "mode": "advanced",
                    "remote": {
                        "provider": "neo4j",
                        "resource": "labels",
                        "params": {},
                        "depends_on": [],
                        "allow_manual": True,
                    },
                },
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
                {
                    "name": "uri",
                    "label": "URI (legacy)",
                    "type": "string",
                    "mode": "advanced",
                    "placeholder": "bolt://localhost:7687",
                },
                {
                    "name": "username",
                    "label": "Username (legacy)",
                    "type": "string",
                    "mode": "advanced",
                },
                {
                    "name": "password",
                    "label": "Password (legacy)",
                    "type": "string",
                    "secret": True,
                    "mode": "advanced",
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

    async def _resolve_uri_auth(self, context: NodeContext) -> tuple[str, tuple[str, str] | None]:
        cred_id = (self.props.credential or "").strip()
        if cred_id:
            data = await resolve_credential(cred_id, context.workspace_id)
            if not data:
                raise ValueError("Neo4j credential not found for this workspace.")
            uri = data.get("uri") or data.get("connectionString") or data.get("host")
            if not uri:
                raise ValueError("Neo4j credential missing uri.")
            uri = str(uri)
            if not uri.startswith(("bolt", "neo4j")):
                uri = f"bolt://{uri}"
            user = data.get("user") or data.get("username")
            pw = data.get("password")
            return uri, (user, pw) if user and pw else None
        if self.props.uri.strip():
            auth = (self.props.username, self.props.password) if self.props.password else None
            return self.props.uri, auth
        raise ValueError("Select a credential or paste URI + password.")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.query.strip():
            return NodeResult(success=False, error="query is required")

        try:
            from neo4j import AsyncGraphDatabase  # type: ignore[import]
        except ImportError:
            return NodeResult(success=False, error="neo4j not installed. Run: pip install neo4j")

        try:
            uri, auth = await self._resolve_uri_auth(context)
        except ValueError as e:
            return NodeResult(success=False, error=str(e))

        params = self._parse_params()
        driver = AsyncGraphDatabase.driver(uri, auth=auth)
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
