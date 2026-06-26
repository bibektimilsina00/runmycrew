"""Shared HTTP + payload utilities for the GitHub node / trigger / webhook.

The action node (`github_node.py`) and polling trigger (`github_trigger.py`)
both need the same primitives:

- A thin GitHub REST v3 client that talks to `https://api.github.com`.
- Optional unauthenticated mode for public-read operations (the 60-req/hr
  shared-IP limit applies, but it's fine for low-volume lookups).
- Pagination + per-page clamping (GitHub caps at 100).
- Friendly flatteners that fold GitHub's verbose payloads into the
  small shapes our `output_data` contract advertises.

This lives next to the node (not under `integrations/github/`) because
it carries GitHub-specific knowledge that's part of the node's contract
rather than a reusable workspace integration. The legacy
`apps.api.app.integrations.github.service` is preserved for the loadOptions
router which already depends on it.
"""

from __future__ import annotations

import re
from typing import Any

import httpx

GITHUB_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"
DEFAULT_TIMEOUT = 30.0


def github_headers(token: str | None) -> dict[str, str]:
    """Standard headers for every GitHub REST v3 call.

    `Accept` pins us to the JSON representation. `X-GitHub-Api-Version`
    locks the response shape against silent upgrades. Token is optional
    — public-read ops (e.g. `GET /repos/{owner}/{repo}` for a public
    repo) work unauthenticated, just rate-limited harder.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def clamp_per_page(value: int | None, default: int = 30) -> int:
    """GitHub caps `per_page` at 100. Anything bigger is silently
    truncated, but the user-facing field shouldn't lie about it.
    """
    if value is None or value <= 0:
        return default
    return min(int(value), 100)


def coerce_owner_repo(value: Any) -> str | None:
    """Resource pickers in the inspector emit either:

      - a bare string (`"acme/web"` typed by hand), OR
      - a `{id, title}` dict (from the loadOptions repo picker).

    Collapse either to the plain string GitHub expects. Returns `None`
    for empty / unparseable input so callers can short-circuit with a
    friendly error.
    """
    if value is None:
        return None
    if isinstance(value, dict):
        candidate = value.get("id") or value.get("full_name") or value.get("name")
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
        return None
    if isinstance(value, str):
        return value.strip() or None
    return None


def parse_csv(value: str | None) -> list[str]:
    """Comma-separated string → list of trimmed non-empty entries."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


# ── error wrapping ──────────────────────────────────────────────────


class GitHubError(Exception):
    """Raised when a GitHub API call returns a non-2xx response.

    Carries the status code separately so the node's `execute()` can
    decide how to surface it (e.g. surface 404 as `"Not found"` vs
    surface 401 as `"Reconnect your GitHub account"`).
    """

    def __init__(self, status: int, message: str, payload: Any = None):
        super().__init__(f"GitHub API error {status}: {message}")
        self.status = status
        self.message = message
        self.payload = payload


def github_error_from_response(resp: httpx.Response) -> GitHubError:
    """Best-effort error extraction from a GitHub error response."""
    try:
        body = resp.json()
        message = (body.get("message") if isinstance(body, dict) else None) or resp.text[:300]
    except Exception:  # noqa: BLE001
        body = resp.text
        message = (resp.text or "")[:300]
    return GitHubError(status=resp.status_code, message=message or "(no body)", payload=body)


async def github_request(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    *,
    token: str | None,
    params: dict[str, Any] | None = None,
    json: Any = None,
    headers_extra: dict[str, str] | None = None,
) -> tuple[Any, dict[str, str]]:
    """Issue one GitHub REST v3 call.

    Returns `(parsed_body, response_headers)` so callers can inspect
    `Link` / `ETag` / `X-RateLimit-Remaining` when they need them
    (pagination cursors, conditional polling). Raises `GitHubError` on
    non-2xx so the caller can rethrow with their own framing.

    `path` should start with `/`. Full URLs (e.g. a `Link: next` href)
    are also accepted — common when iterating GitHub's paginated APIs.
    """
    url = path if path.startswith("http") else f"{GITHUB_BASE_URL}{path}"
    headers = github_headers(token)
    if headers_extra:
        headers.update(headers_extra)
    resp = await client.request(
        method,
        url,
        headers=headers,
        params=params,
        json=json,
        timeout=DEFAULT_TIMEOUT,
    )
    if resp.status_code >= 400:
        raise github_error_from_response(resp)
    body: Any
    if resp.status_code == 204 or not resp.content:
        body = None
    else:
        try:
            body = resp.json()
        except Exception:  # noqa: BLE001
            body = resp.text
    return body, dict(resp.headers)


def parse_link_header(link: str | None) -> dict[str, str]:
    """Split GitHub's `Link` header into a `{rel: url}` map.

    GitHub returns `Link: <https://...?page=2>; rel="next", <...>; rel="last"`.
    Used by the polling trigger to walk past the first page when more
    than 100 items landed since the last cursor.
    """
    if not link:
        return {}
    out: dict[str, str] = {}
    for chunk in link.split(","):
        m = re.match(r'\s*<([^>]+)>;\s*rel="([^"]+)"', chunk)
        if m:
            out[m.group(2)] = m.group(1)
    return out


# ── output flatteners ───────────────────────────────────────────────


def _user_summary(user: Any) -> dict[str, Any] | None:
    """Shrink a GitHub `user` object to the fields workflows actually
    use (login, avatar, profile URL). Drops the dozen verbose URLs.
    """
    if not isinstance(user, dict):
        return None
    return {
        "login": user.get("login"),
        "id": user.get("id"),
        "avatar_url": user.get("avatar_url"),
        "html_url": user.get("html_url"),
        "type": user.get("type"),
    }


def flatten_repo(repo: Any) -> dict[str, Any]:
    """Project a GitHub repo into our canonical shape."""
    if not isinstance(repo, dict):
        return {}
    return {
        "id": repo.get("id"),
        "node_id": repo.get("node_id"),
        "name": repo.get("name"),
        "full_name": repo.get("full_name"),
        "owner": _user_summary(repo.get("owner")),
        "private": repo.get("private"),
        "fork": repo.get("fork"),
        "description": repo.get("description"),
        "html_url": repo.get("html_url"),
        "clone_url": repo.get("clone_url"),
        "ssh_url": repo.get("ssh_url"),
        "default_branch": repo.get("default_branch"),
        "language": repo.get("language"),
        "stargazers_count": repo.get("stargazers_count"),
        "watchers_count": repo.get("watchers_count"),
        "forks_count": repo.get("forks_count"),
        "open_issues_count": repo.get("open_issues_count"),
        "topics": repo.get("topics"),
        "visibility": repo.get("visibility"),
        "archived": repo.get("archived"),
        "created_at": repo.get("created_at"),
        "updated_at": repo.get("updated_at"),
        "pushed_at": repo.get("pushed_at"),
    }


def flatten_issue(issue: Any) -> dict[str, Any]:
    """Issues + pull requests share the same base shape on GitHub —
    PRs are returned with a `pull_request` block on top. We surface
    both via the same flattener and let the caller decide which fields
    to surface to the user.
    """
    if not isinstance(issue, dict):
        return {}
    return {
        "number": issue.get("number"),
        "id": issue.get("id"),
        "title": issue.get("title"),
        "body": issue.get("body"),
        "state": issue.get("state"),
        "html_url": issue.get("html_url"),
        "author": _user_summary(issue.get("user")),
        "assignees": [_user_summary(a) for a in issue.get("assignees") or []],
        "labels": [
            {
                "name": label.get("name"),
                "color": label.get("color"),
                "description": label.get("description"),
            }
            if isinstance(label, dict)
            else label
            for label in issue.get("labels") or []
        ],
        "comments": issue.get("comments"),
        "locked": issue.get("locked"),
        "draft": issue.get("draft"),
        "is_pr": "pull_request" in issue,
        "created_at": issue.get("created_at"),
        "updated_at": issue.get("updated_at"),
        "closed_at": issue.get("closed_at"),
    }


def flatten_comment(comment: Any) -> dict[str, Any]:
    if not isinstance(comment, dict):
        return {}
    return {
        "id": comment.get("id"),
        "body": comment.get("body"),
        "author": _user_summary(comment.get("user")),
        "html_url": comment.get("html_url"),
        "created_at": comment.get("created_at"),
        "updated_at": comment.get("updated_at"),
    }


def flatten_pr(pr: Any) -> dict[str, Any]:
    if not isinstance(pr, dict):
        return {}
    return {
        "number": pr.get("number"),
        "id": pr.get("id"),
        "title": pr.get("title"),
        "body": pr.get("body"),
        "state": pr.get("state"),
        "html_url": pr.get("html_url"),
        "author": _user_summary(pr.get("user")),
        "head": {
            "ref": (pr.get("head") or {}).get("ref"),
            "sha": (pr.get("head") or {}).get("sha"),
            "repo": (pr.get("head") or {}).get("repo", {}).get("full_name"),
        },
        "base": {
            "ref": (pr.get("base") or {}).get("ref"),
            "sha": (pr.get("base") or {}).get("sha"),
            "repo": (pr.get("base") or {}).get("repo", {}).get("full_name"),
        },
        "merged": pr.get("merged"),
        "mergeable": pr.get("mergeable"),
        "draft": pr.get("draft"),
        "additions": pr.get("additions"),
        "deletions": pr.get("deletions"),
        "changed_files": pr.get("changed_files"),
        "labels": [
            label.get("name") if isinstance(label, dict) else label
            for label in pr.get("labels") or []
        ],
        "requested_reviewers": [_user_summary(u) for u in pr.get("requested_reviewers") or []],
        "created_at": pr.get("created_at"),
        "updated_at": pr.get("updated_at"),
        "merged_at": pr.get("merged_at"),
        "closed_at": pr.get("closed_at"),
    }


def flatten_release(rel: Any) -> dict[str, Any]:
    if not isinstance(rel, dict):
        return {}
    return {
        "id": rel.get("id"),
        "tag_name": rel.get("tag_name"),
        "name": rel.get("name"),
        "body": rel.get("body"),
        "draft": rel.get("draft"),
        "prerelease": rel.get("prerelease"),
        "html_url": rel.get("html_url"),
        "author": _user_summary(rel.get("author")),
        "assets": [
            {
                "id": asset.get("id"),
                "name": asset.get("name"),
                "label": asset.get("label"),
                "size": asset.get("size"),
                "browser_download_url": asset.get("browser_download_url"),
            }
            if isinstance(asset, dict)
            else asset
            for asset in rel.get("assets") or []
        ],
        "created_at": rel.get("created_at"),
        "published_at": rel.get("published_at"),
        "target_commitish": rel.get("target_commitish"),
    }


def flatten_commit(commit: Any) -> dict[str, Any]:
    if not isinstance(commit, dict):
        return {}
    commit_obj = commit.get("commit") if isinstance(commit.get("commit"), dict) else {}
    return {
        "sha": commit.get("sha"),
        "node_id": commit.get("node_id"),
        "html_url": commit.get("html_url"),
        "message": commit_obj.get("message") if commit_obj else commit.get("message"),
        "author": _user_summary(commit.get("author"))
        or {
            "login": (commit_obj.get("author") or {}).get("name") if commit_obj else None,
            "email": (commit_obj.get("author") or {}).get("email") if commit_obj else None,
        },
        "committer": _user_summary(commit.get("committer"))
        or {
            "login": (commit_obj.get("committer") or {}).get("name") if commit_obj else None,
            "email": (commit_obj.get("committer") or {}).get("email") if commit_obj else None,
        },
        "date": (commit_obj.get("author") or {}).get("date") if commit_obj else None,
        "stats": commit.get("stats"),
        "files": [
            {
                "filename": f.get("filename"),
                "status": f.get("status"),
                "additions": f.get("additions"),
                "deletions": f.get("deletions"),
                "changes": f.get("changes"),
            }
            if isinstance(f, dict)
            else f
            for f in commit.get("files") or []
        ]
        if commit.get("files")
        else None,
    }


def flatten_branch(branch: Any) -> dict[str, Any]:
    if not isinstance(branch, dict):
        return {}
    commit = branch.get("commit") if isinstance(branch.get("commit"), dict) else {}
    return {
        "name": branch.get("name"),
        "protected": branch.get("protected"),
        "commit_sha": commit.get("sha"),
        "commit_url": commit.get("url"),
    }


def flatten_workflow_run(run: Any) -> dict[str, Any]:
    if not isinstance(run, dict):
        return {}
    return {
        "id": run.get("id"),
        "name": run.get("name"),
        "head_branch": run.get("head_branch"),
        "head_sha": run.get("head_sha"),
        "run_number": run.get("run_number"),
        "event": run.get("event"),
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "workflow_id": run.get("workflow_id"),
        "html_url": run.get("html_url"),
        "actor": _user_summary(run.get("actor")),
        "created_at": run.get("created_at"),
        "updated_at": run.get("updated_at"),
        "run_started_at": run.get("run_started_at"),
    }


def flatten_gist(gist: Any) -> dict[str, Any]:
    if not isinstance(gist, dict):
        return {}
    files = gist.get("files") or {}
    return {
        "id": gist.get("id"),
        "description": gist.get("description"),
        "public": gist.get("public"),
        "html_url": gist.get("html_url"),
        "owner": _user_summary(gist.get("owner")),
        "files": {
            name: {
                "filename": f.get("filename"),
                "language": f.get("language"),
                "type": f.get("type"),
                "size": f.get("size"),
                "raw_url": f.get("raw_url"),
                "content": f.get("content"),  # only present on detail fetch
            }
            for name, f in files.items()
            if isinstance(f, dict)
        },
        "created_at": gist.get("created_at"),
        "updated_at": gist.get("updated_at"),
    }
