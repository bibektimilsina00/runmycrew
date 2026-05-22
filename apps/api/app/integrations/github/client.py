from typing import Any

import httpx

from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)

GITHUB_BASE_URL = "https://api.github.com"


class GitHubClient:
    def __init__(self, access_token: str, client: httpx.AsyncClient | None = None):
        self._access_token = access_token
        self._external_client = client
        self._client = client or httpx.AsyncClient(
            base_url=GITHUB_BASE_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get(self, path: str, params: dict | None = None) -> Any:
        if self._external_client:
            response = await self._external_client.get(
                f"{GITHUB_BASE_URL}{path}", headers=self._headers(), params=params
            )
        else:
            response = await self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def post(self, path: str, json: dict | None = None) -> Any:
        if self._external_client:
            response = await self._external_client.post(
                f"{GITHUB_BASE_URL}{path}", headers=self._headers(), json=json
            )
        else:
            response = await self._client.post(path, json=json)
        response.raise_for_status()
        return response.json()

    async def patch(self, path: str, json: dict | None = None) -> Any:
        if self._external_client:
            response = await self._external_client.patch(
                f"{GITHUB_BASE_URL}{path}", headers=self._headers(), json=json
            )
        else:
            response = await self._client.patch(path, json=json)
        response.raise_for_status()
        return response.json()
