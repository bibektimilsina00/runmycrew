from typing import Any

from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)


class NotionProperties(BaseModel):
    credential: str | None = None
    operation: str = "create_page"
    database_id: str | None = None
    page_id: str | None = None
    title: str | None = None
    properties: Any | None = None
    content: Any | None = None
    filter: Any | None = None
    sorts: Any | None = None
    archived: bool | None = None
    page_size: int = 100


class NotionNode(BaseNode[NotionProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.notion",
            name="Notion",
            category="integration",
            description="Notion integration: manage pages, databases, and content.",
            icon="FileText",
            color="#000000",
            properties=[
                {
                    "name": "credential",
                    "label": "Notion Account",
                    "type": "credential",
                    "credentialType": ["notion_oauth", "notion_api_key"],
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "create_page",
                    "options": [
                        {"label": "Create Page", "value": "create_page"},
                        {"label": "Get Page", "value": "get_page"},
                        {"label": "Update Page", "value": "update_page"},
                        {"label": "Get Page Content", "value": "get_page_content"},
                        {"label": "Append Content to Page", "value": "append_content"},
                        {"label": "Query Database", "value": "query_database"},
                        {"label": "List Databases", "value": "list_databases"},
                    ],
                },
                {
                    "name": "database_id",
                    "label": "Database ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "32-char database ID from Notion URL",
                    "condition": {
                        "field": "operation",
                        "value": ["create_page", "query_database"],
                    },
                    "loadOptions": "/integrations/notion/databases",
                    "loadOptionsDependsOn": ["credential"],
                },
                {
                    "name": "page_id",
                    "label": "Page ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "Page ID from Notion URL",
                    "condition": {
                        "field": "operation",
                        "value": ["get_page", "update_page", "get_page_content", "append_content"],
                    },
                },
                {
                    "name": "title",
                    "label": "Page Title",
                    "type": "string",
                    "required": True,
                    "condition": {"field": "operation", "value": "create_page"},
                },
                {
                    "name": "properties",
                    "label": "Properties (JSON)",
                    "type": "json",
                    "required": False,
                    "placeholder": '{"Status": {"select": {"name": "In Progress"}}}',
                    "condition": {
                        "field": "operation",
                        "value": ["create_page", "update_page"],
                    },
                },
                {
                    "name": "content",
                    "label": "Content Blocks (JSON)",
                    "type": "json",
                    "required": False,
                    "placeholder": '[{"object":"block","type":"paragraph","paragraph":{"rich_text":[{"text":{"content":"Hello"}}]}}]',
                    "mode": "advanced",
                    "condition": {
                        "field": "operation",
                        "value": ["create_page", "append_content"],
                    },
                },
                {
                    "name": "archived",
                    "label": "Archive Page",
                    "type": "boolean",
                    "default": False,
                    "condition": {"field": "operation", "value": "update_page"},
                },
                {
                    "name": "filter",
                    "label": "Filter (JSON)",
                    "type": "json",
                    "required": False,
                    "placeholder": '{"property":"Status","select":{"equals":"Done"}}',
                    "condition": {"field": "operation", "value": "query_database"},
                },
                {
                    "name": "sorts",
                    "label": "Sorts (JSON)",
                    "type": "json",
                    "required": False,
                    "placeholder": '[{"property":"Created","direction":"descending"}]',
                    "mode": "advanced",
                    "condition": {"field": "operation", "value": "query_database"},
                },
                {
                    "name": "page_size",
                    "label": "Page Size",
                    "type": "number",
                    "default": 100,
                    "mode": "advanced",
                    "condition": {"field": "operation", "value": "query_database"},
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "id", "type": "string"},
                {"label": "url", "type": "string"},
                {"label": "title", "type": "string"},
                {"label": "properties", "type": "object"},
                {"label": "results", "type": "array"},
                {"label": "count", "type": "number"},
                {"label": "has_more", "type": "boolean"},
                {"label": "blocks", "type": "array"},
                {"label": "databases", "type": "array"},
            ],
            allow_error=True,
            credential_type=["notion_oauth", "notion_api_key"],
        )

    @classmethod
    def get_properties_model(cls) -> type[NotionProperties]:
        return NotionProperties

    def _get_api_key(self) -> str | None:
        if not self.credential:
            return None
        # OAuth stores access_token; API key stores api_key
        return self.credential.get("access_token") or self.credential.get("api_key")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        try:
            api_key = self._get_api_key()
            if not api_key:
                return NodeResult(
                    success=False,
                    error="Notion credential not found. Please add your Notion API key.",
                )

            from apps.api.app.integrations.notion.service import NotionService

            service = NotionService(api_key=api_key, client=context.http_client)
            op = self.props.operation

            def _clean_id(val: str | None) -> str:
                return (val or "").strip().replace("-", "")

            if op == "create_page":
                database_id = _clean_id(self.props.database_id)
                if not database_id:
                    return NodeResult(success=False, error="database_id is required")
                if not self.props.title:
                    return NodeResult(success=False, error="title is required")

                page = await service.create_page(
                    database_id=database_id,
                    title=self.props.title,
                    properties=self.props.properties,
                    content=self.props.content if isinstance(self.props.content, list) else None,
                )
                return NodeResult(success=True, output_data={
                    "id": page.get("id"),
                    "url": page.get("url"),
                    "title": self.props.title,
                    "properties": page.get("properties", {}),
                })

            elif op == "get_page":
                page_id = _clean_id(self.props.page_id)
                if not page_id:
                    return NodeResult(success=False, error="page_id is required")

                page = await service.get_page(page_id=page_id)
                return NodeResult(success=True, output_data=page)

            elif op == "update_page":
                page_id = _clean_id(self.props.page_id)
                if not page_id:
                    return NodeResult(success=False, error="page_id is required")

                page = await service.update_page(
                    page_id=page_id,
                    properties=self.props.properties,
                    archived=self.props.archived,
                )
                return NodeResult(success=True, output_data=page)

            elif op == "get_page_content":
                page_id = _clean_id(self.props.page_id)
                if not page_id:
                    return NodeResult(success=False, error="page_id is required")

                result = await service.get_page_content(page_id=page_id)
                blocks = result.get("results", [])
                return NodeResult(success=True, output_data={"blocks": blocks, "count": len(blocks)})

            elif op == "append_content":
                page_id = _clean_id(self.props.page_id)
                if not page_id:
                    return NodeResult(success=False, error="page_id is required")

                children = self.props.content
                if not isinstance(children, list):
                    return NodeResult(success=False, error="content must be a JSON array of block objects")

                result = await service.append_block_children(page_id=page_id, children=children)
                return NodeResult(success=True, output_data=result)

            elif op == "query_database":
                database_id = _clean_id(self.props.database_id)
                if not database_id:
                    return NodeResult(success=False, error="database_id is required")

                result = await service.query_database(
                    database_id=database_id,
                    filter=self.props.filter,
                    sorts=self.props.sorts if isinstance(self.props.sorts, list) else None,
                    page_size=self.props.page_size,
                )
                results = result.get("results", [])
                return NodeResult(success=True, output_data={
                    "results": results,
                    "count": len(results),
                    "has_more": result.get("has_more", False),
                    "next_cursor": result.get("next_cursor"),
                })

            elif op == "list_databases":
                databases = await service.list_databases()
                return NodeResult(success=True, output_data={"databases": databases, "count": len(databases)})

            else:
                return NodeResult(success=False, error=f"Unsupported operation: {op}")

        except Exception as e:
            logger.error(f"NotionNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))
