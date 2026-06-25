from __future__ import annotations

import json
from contextlib import suppress
from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class MongoDBProperties(BaseModel):
    connectionString: str = ""
    database: str = ""
    collection: str = ""
    operation: str = "find"  # find | findOne | insertOne | updateOne | deleteOne | aggregate
    query: Any = None  # filter / document depending on operation
    update: Any = None  # update document for updateOne
    limit: int = 100


class MongoDBNode(BaseNode[MongoDBProperties]):
    @classmethod
    def get_properties_model(cls) -> type[MongoDBProperties]:
        return MongoDBProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.mongodb",
            name="MongoDB",
            category="integration",
            description="Query or mutate a MongoDB collection.",
            icon="mongodb",
            color="#1c1c1c",
            properties=[
                {
                    "name": "connectionString",
                    "label": "Connection String",
                    "type": "string",
                    "required": True,
                    "placeholder": "mongodb://user:pass@host:27017",
                },
                {
                    "name": "database",
                    "label": "Database",
                    "type": "string",
                    "required": True,
                },
                {
                    "name": "collection",
                    "label": "Collection",
                    "type": "string",
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "find",
                    "options": [
                        {"label": "Find", "value": "find"},
                        {"label": "Find One", "value": "findOne"},
                        {"label": "Insert One", "value": "insertOne"},
                        {"label": "Update One", "value": "updateOne"},
                        {"label": "Delete One", "value": "deleteOne"},
                        {"label": "Aggregate", "value": "aggregate"},
                    ],
                },
                {
                    "name": "query",
                    "label": "Filter / Document / Pipeline",
                    "type": "json",
                    "default": {},
                    "description": "Filter for find/update/delete, document for insert, pipeline array for aggregate.",
                },
                {
                    "name": "update",
                    "label": "Update",
                    "type": "json",
                    "default": {},
                    "description": "Update document for updateOne (e.g. {$set: {...}}).",
                    "condition": {"field": "operation", "value": "updateOne"},
                },
                {
                    "name": "limit",
                    "label": "Limit",
                    "type": "number",
                    "default": 100,
                    "mode": "advanced",
                    "condition": {"field": "operation", "value": "find"},
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "documents", "type": "array"},
                {"label": "count", "type": "number"},
                {"label": "insertedId", "type": "string"},
            ],
            allow_error=True,
        )

    def _parse_json_prop(self, raw: Any) -> Any:
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {}
        return raw or {}

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.connectionString.strip():
            return NodeResult(success=False, error="connectionString is required")
        if not self.props.database.strip():
            return NodeResult(success=False, error="database is required")
        if not self.props.collection.strip():
            return NodeResult(success=False, error="collection is required")

        try:
            import motor.motor_asyncio as motor
        except ImportError:
            return NodeResult(success=False, error="motor not installed. Run: pip install motor")

        query = self._parse_json_prop(self.props.query)
        update = self._parse_json_prop(self.props.update)

        try:
            client = motor.AsyncIOMotorClient(self.props.connectionString)
            db = client[self.props.database]
            coll = db[self.props.collection]

            op = self.props.operation
            if op == "find":
                cursor = coll.find(query).limit(self.props.limit)
                docs = await cursor.to_list(length=self.props.limit)
                # Convert ObjectId to str
                docs = [self._serialize_doc(d) for d in docs]
                return NodeResult(success=True, output_data={"documents": docs, "count": len(docs)})

            elif op == "findOne":
                doc = await coll.find_one(query)
                doc = self._serialize_doc(doc) if doc else None
                return NodeResult(
                    success=True,
                    output_data={"documents": [doc] if doc else [], "count": 1 if doc else 0},
                )

            elif op == "insertOne":
                result = await coll.insert_one(query)
                return NodeResult(
                    success=True,
                    output_data={
                        "documents": [],
                        "count": 1,
                        "insertedId": str(result.inserted_id),
                    },
                )

            elif op == "updateOne":
                result = await coll.update_one(query, update)
                return NodeResult(
                    success=True,
                    output_data={
                        "documents": [],
                        "count": result.modified_count,
                        "matchedCount": result.matched_count,
                    },
                )

            elif op == "deleteOne":
                result = await coll.delete_one(query)
                return NodeResult(
                    success=True, output_data={"documents": [], "count": result.deleted_count}
                )

            elif op == "aggregate":
                pipeline = query if isinstance(query, list) else []
                cursor = coll.aggregate(pipeline)
                docs = await cursor.to_list(length=self.props.limit)
                docs = [self._serialize_doc(d) for d in docs]
                return NodeResult(success=True, output_data={"documents": docs, "count": len(docs)})

            else:
                return NodeResult(success=False, error=f"Unknown operation: {op}")

        except Exception as e:
            return NodeResult(success=False, error=f"MongoDB error: {e}")
        finally:
            with suppress(Exception):
                client.close()

    def _serialize_doc(self, doc: dict[str, Any]) -> dict[str, Any]:
        result = {}
        for k, v in doc.items():
            if hasattr(v, "__str__") and type(v).__name__ == "ObjectId":
                result[k] = str(v)
            else:
                result[k] = v
        return result
