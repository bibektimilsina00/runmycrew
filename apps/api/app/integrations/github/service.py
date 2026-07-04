from typing import Any

import httpx

from apps.api.app.core.logger import get_logger
from apps.api.app.integrations.github.client import GitHubClient

logger = get_logger(__name__)


class GitHubService:
    def __init__(self, access_token: str, client: httpx.AsyncClient | None = None):
        self._client = GitHubClient(access_token=access_token, client=client)

    async def get_authenticated_user(self) -> dict:
        return await self._client.get("/user")

    async def list_repos(self, per_page: int = 100, page: int = 1) -> list:
        return await self._client.get(
            "/user/repos",
            params={"per_page": min(per_page, 100), "page": page, "sort": "updated"},
        )

    async def get_repo(self, owner: str, repo: str) -> dict:
        return await self._client.get(f"/repos/{owner}/{repo}")

    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> dict:
        payload: dict[str, Any] = {"title": title}
        if body:
            payload["body"] = body
        if labels:
            payload["labels"] = labels
        if assignees:
            payload["assignees"] = assignees
        return await self._client.post(f"/repos/{owner}/{repo}/issues", json=payload)

    async def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: str | None = None,
        per_page: int = 30,
    ) -> list:
        params: dict[str, Any] = {"state": state, "per_page": min(per_page, 100)}
        if labels:
            params["labels"] = labels
        return await self._client.get(f"/repos/{owner}/{repo}/issues", params=params)

    async def get_issue(self, owner: str, repo: str, issue_number: int) -> dict:
        return await self._client.get(f"/repos/{owner}/{repo}/issues/{issue_number}")

    async def update_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
        labels: list[str] | None = None,
    ) -> dict:
        payload: dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if body is not None:
            payload["body"] = body
        if state is not None:
            payload["state"] = state
        if labels is not None:
            payload["labels"] = labels
        return await self._client.patch(
            f"/repos/{owner}/{repo}/issues/{issue_number}", json=payload
        )

    async def add_comment(self, owner: str, repo: str, issue_number: int, body: str) -> dict:
        return await self._client.post(
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            json={"body": body},
        )

    async def list_comments(self, owner: str, repo: str, issue_number: int) -> list:
        return await self._client.get(f"/repos/{owner}/{repo}/issues/{issue_number}/comments")

    async def list_branches(self, owner: str, repo: str, per_page: int = 100) -> list:
        return await self._client.get(
            f"/repos/{owner}/{repo}/branches",
            params={"per_page": min(per_page, 100)},
        )

    async def list_open_issues(self, owner: str, repo: str, per_page: int = 50) -> list:
        # Filter to non-PR issues; GitHub's /issues endpoint returns
        # both kinds and tags PR-issues with a `pull_request` field.
        items = await self._client.get(
            f"/repos/{owner}/{repo}/issues",
            params={"state": "open", "per_page": min(per_page, 100)},
        )
        return [i for i in items or [] if isinstance(i, dict) and "pull_request" not in i]

    async def list_open_prs(self, owner: str, repo: str, per_page: int = 50) -> list:
        return await self._client.get(
            f"/repos/{owner}/{repo}/pulls",
            params={"state": "open", "per_page": min(per_page, 100)},
        )
