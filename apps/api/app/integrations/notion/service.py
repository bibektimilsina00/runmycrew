import httpx
from typing import Any

from apps.api.app.integrations.notion.client import NotionClient
from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)


class NotionService:
    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None):
        self._client = NotionClient(api_key=api_key, client=client)

    async def list_databases(self) -> list:
        result = await self._client.post("/search", json={
            "filter": {"value": "database", "property": "object"},
            "sort": {"direction": "descending", "timestamp": "last_edited_time"},
        })
        return result.get("results", [])

    async def get_database(self, database_id: str) -> dict:
        return await self._client.get(f"/databases/{database_id}")

    async def query_database(
        self,
        database_id: str,
        filter: dict | None = None,
        sorts: list | None = None,
        page_size: int = 100,
        start_cursor: str | None = None,
    ) -> dict:
        payload: dict[str, Any] = {"page_size": min(page_size, 100)}
        if filter:
            payload["filter"] = filter
        if sorts:
            payload["sorts"] = sorts
        if start_cursor:
            payload["start_cursor"] = start_cursor
        return await self._client.post(f"/databases/{database_id}/query", json=payload)

    async def create_page(
        self,
        database_id: str,
        title: str,
        properties: dict | None = None,
        content: list | None = None,
    ) -> dict:
        page_properties: dict[str, Any] = {
            "title": {
                "title": [{"type": "text", "text": {"content": title}}]
            }
        }
        if properties:
            page_properties.update(properties)

        payload: dict[str, Any] = {
            "parent": {"database_id": database_id},
            "properties": page_properties,
        }
        if content:
            payload["children"] = content

        return await self._client.post("/pages", json=payload)

    async def get_page(self, page_id: str) -> dict:
        return await self._client.get(f"/pages/{page_id}")

    async def update_page(
        self,
        page_id: str,
        properties: dict | None = None,
        archived: bool | None = None,
    ) -> dict:
        payload: dict[str, Any] = {}
        if properties:
            payload["properties"] = properties
        if archived is not None:
            payload["archived"] = archived
        return await self._client.patch(f"/pages/{page_id}", json=payload)

    async def get_page_content(self, page_id: str) -> dict:
        return await self._client.get(f"/blocks/{page_id}/children")

    async def append_block_children(self, page_id: str, children: list) -> dict:
        return await self._client.patch(
            f"/blocks/{page_id}/children",
            json={"children": children},
        )
