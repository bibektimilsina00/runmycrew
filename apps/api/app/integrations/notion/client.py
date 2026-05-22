from typing import Any

import httpx

from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)

NOTION_BASE_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class NotionClient:
    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None):
        self._api_key = api_key
        self._external_client = client
        self._client = client or httpx.AsyncClient(
            base_url=NOTION_BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    async def get(self, path: str, params: dict | None = None) -> Any:
        if self._external_client:
            response = await self._external_client.get(
                f"{NOTION_BASE_URL}{path}", headers=self._headers(), params=params
            )
        else:
            response = await self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def post(self, path: str, json: dict | None = None) -> Any:
        if self._external_client:
            response = await self._external_client.post(
                f"{NOTION_BASE_URL}{path}", headers=self._headers(), json=json or {}
            )
        else:
            response = await self._client.post(path, json=json or {})
        response.raise_for_status()
        return response.json()

    async def patch(self, path: str, json: dict | None = None) -> Any:
        if self._external_client:
            response = await self._external_client.patch(
                f"{NOTION_BASE_URL}{path}", headers=self._headers(), json=json or {}
            )
        else:
            response = await self._client.patch(path, json=json or {})
        response.raise_for_status()
        return response.json()
