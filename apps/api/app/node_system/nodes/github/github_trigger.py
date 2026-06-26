"""GitHub polling trigger — fires on new issues, PRs, comments, releases, commits.

Cursor model
  - First poll snapshots the current set of items and persists their ids /
    timestamps without emitting anything. Workflows should only fire on what
    arrives AFTER the trigger was wired — not on whatever was already there.
  - Subsequent polls diff against the cursor and emit one execution per new
    item. The cursor advances atomically with the dispatch so a crash between
    the two only re-emits, never skips.

The scheduler hands each tick `(token, cursor, props)` and expects
`(matches, new_cursor)`. Polling cadence is per-row via
`integration_trigger_state.next_poll_at`, identical to Gmail / Calendar.

Webhook trigger lives in `github_webhook.py` — same node-set, different
delivery mechanism. The webhook is preferable when the customer can expose
a public URL; polling is the fallback for firewalled installs and for
read-only PATs that can't subscribe to webhooks.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel, field_validator

from apps.api.app.core.logger import get_logger
from apps.api.app.features.triggers.repository import IntegrationTriggerStateRepository
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.github.github_helpers import (
    GitHubError,
    coerce_owner_repo,
    flatten_comment,
    flatten_commit,
    flatten_issue,
    flatten_pr,
    flatten_release,
    github_request,
)

logger = get_logger(__name__)

PROVIDER = "github"
DEFAULT_POLL_INTERVAL_SECONDS = 120

EVENT_NEW_ISSUE = "new_issue"
EVENT_NEW_PR = "new_pr"
EVENT_NEW_ISSUE_COMMENT = "new_issue_comment"
EVENT_NEW_RELEASE = "new_release"
EVENT_NEW_COMMIT = "new_commit"
EVENT_TYPES = (
    EVENT_NEW_ISSUE,
    EVENT_NEW_PR,
    EVENT_NEW_ISSUE_COMMENT,
    EVENT_NEW_RELEASE,
    EVENT_NEW_COMMIT,
)


class GitHubTriggerProperties(BaseModel):
    credential: str | None = None
    event_type: str = EVENT_NEW_ISSUE
    owner: str = ""
    repo: str = ""
    # new_commit only — optional, falls back to the repo's default branch.
    branch: str = ""
    max_per_poll: int = 25
    poll_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS

    @field_validator("owner", "repo", "branch", mode="before")
    @classmethod
    def _coerce_picker(cls, value: Any) -> str:
        if isinstance(value, dict):
            v = value.get("name") or value.get("value") or value.get("id")
            return str(v) if isinstance(v, str) else ""
        return str(value or "")

    @field_validator("event_type", mode="before")
    @classmethod
    def _coerce_event_type(cls, value: Any) -> str:
        v = str(value or "").strip().lower()
        return v if v in EVENT_TYPES else EVENT_NEW_ISSUE


class GitHubTriggerNode(BaseNode[GitHubTriggerProperties]):
    @classmethod
    def get_properties_model(cls):
        return GitHubTriggerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.github",
            name="GitHub",
            category="trigger",
            description=(
                "Polls a GitHub repo for new issues, pull requests, issue "
                "comments, releases, or commits. First poll snapshots silently; "
                "later polls emit one execution per new item. Use the GitHub "
                "Webhook trigger instead when you can expose a public URL."
            ),
            icon="github",
            color="#ffffff",
            credential_type=["github_oauth", "github_pat"],
            properties=[
                {
                    "name": "credential",
                    "label": "GitHub Account",
                    "type": "credential",
                    "credentialType": ["github_oauth", "github_pat"],
                    "required": True,
                },
                {
                    "name": "event_type",
                    "label": "Event",
                    "type": "options",
                    "default": EVENT_NEW_ISSUE,
                    "options": [
                        {"label": "New issue", "value": EVENT_NEW_ISSUE},
                        {"label": "New pull request", "value": EVENT_NEW_PR},
                        {"label": "New issue / PR comment", "value": EVENT_NEW_ISSUE_COMMENT},
                        {"label": "New release", "value": EVENT_NEW_RELEASE},
                        {"label": "New commit", "value": EVENT_NEW_COMMIT},
                    ],
                },
                {
                    "name": "owner",
                    "label": "Owner (user or org)",
                    "type": "string",
                    "required": True,
                    "placeholder": "octocat",
                },
                {
                    "name": "repo",
                    "label": "Repository",
                    "type": "string",
                    "required": True,
                    "placeholder": "hello-world",
                    "loadOptions": "/integrations/github/repos",
                    "loadOptionsDependsOn": ["credential", "owner"],
                },
                {
                    "name": "branch",
                    "label": "Branch (optional)",
                    "type": "string",
                    "placeholder": "main",
                    "description": "Leave blank to track the repo's default branch.",
                    "loadOptions": "/integrations/github/branches",
                    "loadOptionsDependsOn": ["credential", "owner", "repo"],
                    "condition": {"field": "event_type", "value": EVENT_NEW_COMMIT},
                },
                {
                    "name": "max_per_poll",
                    "label": "Max events per poll",
                    "type": "number",
                    "default": 25,
                    "mode": "advanced",
                },
                {
                    "name": "poll_interval_seconds",
                    "label": "Poll interval (seconds)",
                    "type": "number",
                    "default": DEFAULT_POLL_INTERVAL_SECONDS,
                    "description": "Min 30s. GitHub's unauthenticated rate limit is 60/hr.",
                    "mode": "advanced",
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "id", "type": "string"},
                {"label": "number", "type": "number"},
                {"label": "title", "type": "string"},
                {"label": "event_type", "type": "string"},
                {"label": "html_url", "type": "string"},
                {"label": "author", "type": "object"},
            ],
            allow_error=True,
        )

    def _get_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        # Scheduler-dispatched runs hand us the matched event payload directly.
        # Pass it through so downstream nodes see the same shape `/listen`
        # returned on the test poll.
        if (
            isinstance(input_data, dict)
            and input_data.get("event_type") in EVENT_TYPES
            and (input_data.get("id") is not None or input_data.get("sha") is not None)
        ):
            return NodeResult(success=True, output_data=input_data)

        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="GitHub credential required.")

        owner = coerce_owner_repo(self.props.owner) or ""
        repo = coerce_owner_repo(self.props.repo) or ""
        if not (owner and repo):
            return NodeResult(success=False, error="Owner and repo are required.")

        workflow_id = getattr(context, "workflow_id", None)
        node_id = getattr(context, "node_id", None)
        workspace_id = getattr(context, "workspace_id", None)
        db = getattr(context, "db", None)
        wf_uuid = _safe_uuid(workflow_id)
        ws_uuid = _safe_uuid(workspace_id)

        if wf_uuid is None or ws_uuid is None or db is None or not node_id:
            return await self._stateless_preview(token, owner, repo)

        repo_ = IntegrationTriggerStateRepository(db)
        state = await repo_.get(wf_uuid, node_id)
        cursor = state.cursor if state else None

        try:
            matches, new_cursor = await self.poll(token, owner, repo, cursor)
        except GitHubError as exc:
            return NodeResult(success=False, error=f"GitHub API error {exc.status}: {exc.message}")
        except httpx.HTTPError as exc:
            return NodeResult(success=False, error=f"GitHub network error: {exc}")
        except Exception as exc:  # noqa: BLE001
            logger.error("GitHubTriggerNode poll failed: %s", exc, exc_info=True)
            return NodeResult(success=False, error=str(exc))

        await repo_.upsert(
            workflow_id=wf_uuid,
            workspace_id=ws_uuid,
            node_id=node_id,
            provider=PROVIDER,
            cursor=new_cursor,
            next_poll_at=_next_poll_at(self.props.poll_interval_seconds),
            last_error=None,
        )
        await db.commit()

        if not matches:
            return NodeResult(
                success=True,
                output_data={
                    "matched": 0,
                    "items": [],
                    **_cursor_summary(new_cursor),
                },
                handled_successors=True,
            )
        return NodeResult(success=True, output_data=matches[0])

    async def poll(
        self,
        token: str,
        owner: str,
        repo: str,
        cursor: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        event_type = self.props.event_type
        prior_event = (cursor or {}).get("event_type")
        prior_repo = (cursor or {}).get("repo")
        full_repo = f"{owner}/{repo}"
        # Reset the cursor when the user repoints the trigger at a
        # different event / repo — otherwise stale known_ids would silence
        # the next poll.
        if cursor and (prior_event != event_type or prior_repo != full_repo):
            cursor = None

        async with httpx.AsyncClient(timeout=30) as client:
            if event_type == EVENT_NEW_ISSUE:
                return await self._poll_issues(client, token, owner, repo, cursor)
            if event_type == EVENT_NEW_PR:
                return await self._poll_prs(client, token, owner, repo, cursor)
            if event_type == EVENT_NEW_ISSUE_COMMENT:
                return await self._poll_issue_comments(client, token, owner, repo, cursor)
            if event_type == EVENT_NEW_RELEASE:
                return await self._poll_releases(client, token, owner, repo, cursor)
            if event_type == EVENT_NEW_COMMIT:
                return await self._poll_commits(client, token, owner, repo, cursor)
        return [], {"event_type": event_type, "repo": full_repo}

    async def _poll_issues(
        self,
        client: httpx.AsyncClient,
        token: str,
        owner: str,
        repo: str,
        cursor: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        body, _ = await github_request(
            client,
            "GET",
            f"/repos/{owner}/{repo}/issues",
            token=token,
            params={"state": "all", "sort": "created", "direction": "desc", "per_page": 100},
        )
        # /issues returns PR-issues too; strip them — PRs have their own event.
        items = [i for i in (body or []) if isinstance(i, dict) and "pull_request" not in i]
        return self._diff_by_id(items, cursor, EVENT_NEW_ISSUE, owner, repo, flatten_issue)

    async def _poll_prs(
        self,
        client: httpx.AsyncClient,
        token: str,
        owner: str,
        repo: str,
        cursor: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        body, _ = await github_request(
            client,
            "GET",
            f"/repos/{owner}/{repo}/pulls",
            token=token,
            params={"state": "all", "sort": "created", "direction": "desc", "per_page": 100},
        )
        return self._diff_by_id(body or [], cursor, EVENT_NEW_PR, owner, repo, flatten_pr)

    async def _poll_issue_comments(
        self,
        client: httpx.AsyncClient,
        token: str,
        owner: str,
        repo: str,
        cursor: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        params: dict[str, Any] = {
            "sort": "created",
            "direction": "desc",
            "per_page": 100,
        }
        since = (cursor or {}).get("since")
        if since:
            params["since"] = since
        body, _ = await github_request(
            client,
            "GET",
            f"/repos/{owner}/{repo}/issues/comments",
            token=token,
            params=params,
        )
        return self._diff_by_id(
            body or [], cursor, EVENT_NEW_ISSUE_COMMENT, owner, repo, flatten_comment
        )

    async def _poll_releases(
        self,
        client: httpx.AsyncClient,
        token: str,
        owner: str,
        repo: str,
        cursor: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        body, _ = await github_request(
            client,
            "GET",
            f"/repos/{owner}/{repo}/releases",
            token=token,
            params={"per_page": 30},
        )
        return self._diff_by_id(body or [], cursor, EVENT_NEW_RELEASE, owner, repo, flatten_release)

    async def _poll_commits(
        self,
        client: httpx.AsyncClient,
        token: str,
        owner: str,
        repo: str,
        cursor: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        branch = (self.props.branch or "").strip()
        params: dict[str, Any] = {"per_page": 50}
        if branch:
            params["sha"] = branch
        since = (cursor or {}).get("since")
        if since:
            params["since"] = since
        body, _ = await github_request(
            client,
            "GET",
            f"/repos/{owner}/{repo}/commits",
            token=token,
            params=params,
        )
        commits = body or []
        full_repo = f"{owner}/{repo}"
        max_per = max(1, min(int(self.props.max_per_poll or 25), 100))
        # Commits use sha (not numeric id). Track recent shas to dedup.
        prior_ids = (cursor or {}).get("known_ids")
        if not isinstance(prior_ids, list):
            return [], {
                "event_type": EVENT_NEW_COMMIT,
                "repo": full_repo,
                "branch": branch,
                "known_ids": [str(c.get("sha")) for c in commits if c.get("sha")][:200],
                "since": _utc_now_rfc3339(),
            }
        known = set(prior_ids)
        matches: list[dict[str, Any]] = []
        seen: set[str] = set()
        # Oldest first so workflow execution order matches commit order.
        for commit in reversed(commits):
            sha = str(commit.get("sha") or "")
            if not sha or sha in known:
                continue
            matches.append(
                {
                    **flatten_commit(commit),
                    "event_type": EVENT_NEW_COMMIT,
                    "branch": branch,
                    "repo": full_repo,
                }
            )
            seen.add(sha)
            if len(matches) >= max_per:
                break
        merged = list(known | seen)
        # Keep the cursor bounded — only the last 500 shas.
        if len(merged) > 500:
            merged = merged[-500:]
        return matches, {
            "event_type": EVENT_NEW_COMMIT,
            "repo": full_repo,
            "branch": branch,
            "known_ids": merged,
            "since": _utc_now_rfc3339(),
        }

    def _diff_by_id(
        self,
        items: list[dict[str, Any]],
        cursor: dict[str, Any] | None,
        event_type: str,
        owner: str,
        repo: str,
        flatten: Any,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Generic `seen-id` dedup for events keyed by numeric `id`."""
        max_per = max(1, min(int(self.props.max_per_poll or 25), 100))
        full_repo = f"{owner}/{repo}"
        ids_now = [str(i.get("id")) for i in items if isinstance(i, dict) and i.get("id")]
        prior_ids = (cursor or {}).get("known_ids")
        if not isinstance(prior_ids, list):
            return [], {
                "event_type": event_type,
                "repo": full_repo,
                "known_ids": ids_now[:500],
                "since": _utc_now_rfc3339(),
            }
        known = set(prior_ids)
        matches: list[dict[str, Any]] = []
        seen: set[str] = set()
        # Oldest first so the first execution carries the oldest item.
        for item in reversed(items):
            iid = str(item.get("id") or "")
            if not iid or iid in known:
                continue
            matches.append(
                {
                    **flatten(item),
                    "event_type": event_type,
                    "repo": full_repo,
                }
            )
            seen.add(iid)
            if len(matches) >= max_per:
                break
        merged = list(known | seen)
        if len(merged) > 500:
            merged = merged[-500:]
        return matches, {
            "event_type": event_type,
            "repo": full_repo,
            "known_ids": merged,
            "since": _utc_now_rfc3339(),
        }

    async def _stateless_preview(self, token: str, owner: str, repo: str) -> NodeResult:
        """Editor preview path — return the most recent matching item."""
        matches, _ = await self.poll(token, owner, repo, None)
        if not matches:
            # First-poll snapshot returned no matches — pull a real preview by
            # priming the cursor with the prior event tag so the diff runs.
            primer = {
                "event_type": self.props.event_type,
                "repo": f"{owner}/{repo}",
                "known_ids": [],
                "since": "",
            }
            matches, _ = await self.poll(token, owner, repo, primer)
        if not matches:
            return NodeResult(
                success=True,
                output_data={"matched": 0, "event_type": self.props.event_type},
                handled_successors=True,
            )
        return NodeResult(success=True, output_data=matches[0])


def _safe_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None


def _next_poll_at(interval_seconds: int) -> datetime:
    seconds = max(30, min(int(interval_seconds or DEFAULT_POLL_INTERVAL_SECONDS), 60 * 60))
    return datetime.now(UTC) + timedelta(seconds=seconds)


def _utc_now_rfc3339() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _cursor_summary(cursor: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_type": cursor.get("event_type"),
        "repo": cursor.get("repo"),
        "tracked_ids": len(cursor.get("known_ids") or []),
    }


async def _poll_for_scheduler(
    token: str,
    cursor: dict[str, Any] | None,
    props: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    node = GitHubTriggerNode.__new__(GitHubTriggerNode)
    node.props = GitHubTriggerProperties(
        credential=None,
        event_type=str(props.get("event_type") or EVENT_NEW_ISSUE),
        owner=str(props.get("owner") or ""),
        repo=str(props.get("repo") or ""),
        branch=str(props.get("branch") or ""),
        max_per_poll=int(props.get("max_per_poll") or 25),
        poll_interval_seconds=int(
            props.get("poll_interval_seconds") or DEFAULT_POLL_INTERVAL_SECONDS
        ),
    )
    owner = coerce_owner_repo(node.props.owner) or ""
    repo = coerce_owner_repo(node.props.repo) or ""
    if not (owner and repo):
        return [], {"event_type": node.props.event_type, "repo": ""}
    return await node.poll(token, owner, repo, cursor)


def _register() -> None:
    try:
        from apps.api.app.execution_engine.scheduler.integration_polling import (
            register_poller,
        )
    except Exception:  # noqa: BLE001
        return
    register_poller(
        node_type="trigger.github",
        provider=PROVIDER,
        poller=_poll_for_scheduler,
    )


_register()
