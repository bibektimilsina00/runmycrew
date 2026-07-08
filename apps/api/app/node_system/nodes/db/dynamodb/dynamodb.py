from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class DynamoDBProperties(BaseModel):
    region: str = "us-east-1"
    accessKeyId: str = ""
    secretAccessKey: str = ""
    tableName: str = ""
    operation: str = "get_item"  # get_item | put_item | query | scan | delete_item
    key: Any = None  # primary key for get/delete
    item: Any = None  # item for put_item
    keyCondition: str = ""  # KeyConditionExpression for query
    expressionValues: Any = None  # ExpressionAttributeValues


class DynamoDBNode(BaseNode[DynamoDBProperties]):
    @classmethod
    def get_properties_model(cls) -> type[DynamoDBProperties]:
        return DynamoDBProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.dynamodb",
            name="DynamoDB",
            category="integration",
            description="Query or mutate an AWS DynamoDB table.",
            icon="dynamodb",
            color="#ffffff",
            properties=[
                {"name": "region", "label": "AWS Region", "type": "string", "default": "us-east-1"},
                {
                    "name": "accessKeyId",
                    "label": "Access Key ID",
                    "type": "string",
                    "required": True,
                },
                {
                    "name": "secretAccessKey",
                    "label": "Secret Access Key",
                    "type": "string",
                    "required": True,
                },
                {"name": "tableName", "label": "Table Name", "type": "string", "required": True},
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "get_item",
                    "options": [
                        {"label": "Get Item", "value": "get_item"},
                        {"label": "Put Item", "value": "put_item"},
                        {"label": "Query", "value": "query"},
                        {"label": "Scan", "value": "scan"},
                        {"label": "Delete Item", "value": "delete_item"},
                    ],
                },
                {
                    "name": "key",
                    "label": "Key",
                    "type": "json",
                    "default": {},
                    "description": "Primary key for get/delete.",
                    "condition": {"field": "operation", "value": "get_item"},
                },
                {
                    "name": "item",
                    "label": "Item",
                    "type": "json",
                    "default": {},
                    "condition": {"field": "operation", "value": "put_item"},
                },
                {
                    "name": "keyCondition",
                    "label": "Key Condition Expression",
                    "type": "string",
                    "condition": {"field": "operation", "value": "query"},
                },
                {
                    "name": "expressionValues",
                    "label": "Expression Attribute Values",
                    "type": "json",
                    "condition": {"field": "operation", "value": "query"},
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "item", "type": "object"},
                {"label": "items", "type": "array"},
                {"label": "count", "type": "number"},
            ],
            allow_error=True,
        )

    def _parse(self, raw: Any) -> Any:
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {}
        return raw or {}

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.tableName.strip():
            return NodeResult(success=False, error="tableName is required")

        try:
            import aioboto3  # type: ignore[import]
        except ImportError:
            return NodeResult(
                success=False, error="aioboto3 not installed. Run: pip install aioboto3"
            )

        session = aioboto3.Session(
            aws_access_key_id=self.props.accessKeyId,
            aws_secret_access_key=self.props.secretAccessKey,
            region_name=self.props.region,
        )
        op = self.props.operation
        table_name = self.props.tableName.strip()

        try:
            async with session.resource("dynamodb") as dynamodb:
                table = await dynamodb.Table(table_name)

                if op == "get_item":
                    resp = await table.get_item(Key=self._parse(self.props.key))
                    item = resp.get("Item", {})
                    return NodeResult(
                        success=True,
                        output_data={
                            "item": item,
                            "items": [item] if item else [],
                            "count": 1 if item else 0,
                        },
                    )

                elif op == "put_item":
                    await table.put_item(Item=self._parse(self.props.item))
                    return NodeResult(
                        success=True, output_data={"item": {}, "items": [], "count": 1}
                    )

                elif op == "query":
                    kwargs: dict[str, Any] = {"KeyConditionExpression": self.props.keyCondition}
                    expr_vals = self._parse(self.props.expressionValues)
                    if expr_vals:
                        kwargs["ExpressionAttributeValues"] = expr_vals
                    resp = await table.query(**kwargs)
                    items = resp.get("Items", [])
                    return NodeResult(
                        success=True,
                        output_data={
                            "item": items[0] if items else {},
                            "items": items,
                            "count": len(items),
                        },
                    )

                elif op == "scan":
                    resp = await table.scan()
                    items = resp.get("Items", [])
                    return NodeResult(
                        success=True,
                        output_data={
                            "item": items[0] if items else {},
                            "items": items,
                            "count": len(items),
                        },
                    )

                elif op == "delete_item":
                    await table.delete_item(Key=self._parse(self.props.key))
                    return NodeResult(
                        success=True, output_data={"item": {}, "items": [], "count": 1}
                    )

                else:
                    return NodeResult(success=False, error=f"Unknown operation: {op}")

        except Exception as e:
            return NodeResult(success=False, error=f"DynamoDB error: {e}")
