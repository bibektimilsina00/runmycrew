"""GitHub action node — 56 ops across the public REST API surface.

Resources covered: issues, comments, pull requests, repositories,
branches, files, releases, tags, commits, workflows, users, gists,
search. A handful of operations are flagged *public* — they read
data anyone could fetch with `curl https://api.github.com/...`, so the
inspector hides the credential picker for them and `execute()` skips
the access-token check. That mirrors the YouTube node's
`get_public_video` / `get_video_transcript` pattern.

Lookup contract:
- backend metadata is the contract; the inspector picks ops + auth
  visibility from `_PUBLIC_OPS` and the `condition` blocks below
- field validators collapse the picker `{id, title}` shape down to
  the bare string GitHub expects
- `_HANDLERS` is the dispatch table; one entry per op keeps the body
  of `execute()` a one-liner.
"""

from __future__ import annotations

import base64
import re
from typing import Any

import httpx
from pydantic import BaseModel, field_validator

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.github.github_helpers import (
    GitHubError,
    clamp_per_page,
    coerce_owner_repo,
    flatten_branch,
    flatten_comment,
    flatten_commit,
    flatten_gist,
    flatten_issue,
    flatten_pr,
    flatten_release,
    flatten_repo,
    flatten_workflow_run,
    github_request,
    parse_csv,
)

logger = get_logger(__name__)


# ── operation buckets used by the inspector's `condition` blocks ──

_PUBLIC_OPS = (
    "get_public_repo",
    "get_public_file",
    "list_user_public_repos",
    "search_public_code",
)

_NEED_OWNER_REPO_OPS = (
    "create_issue",
    "get_issue",
    "update_issue",
    "list_issues",
    "lock_issue",
    "unlock_issue",
    "add_comment",
    "list_comments",
    "update_comment",
    "delete_comment",
    "create_pr",
    "get_pr",
    "update_pr",
    "list_prs",
    "merge_pr",
    "request_review",
    "list_reviews",
    "add_pr_comment",
    "get_repo",
    "delete_repo",
    "star_repo",
    "unstar_repo",
    "create_branch",
    "get_branch",
    "list_branches",
    "delete_branch",
    "get_default_branch",
    "get_file_content",
    "create_file",
    "update_file",
    "delete_file",
    "list_dir",
    "create_release",
    "get_release",
    "list_releases",
    "update_release",
    "delete_release",
    "create_tag",
    "list_tags",
    "get_commit",
    "list_commits",
    "compare_commits",
    "list_workflows",
    "get_workflow_run",
    "dispatch_workflow",
    "cancel_workflow_run",
    "rerun_workflow",
)

_NEED_ISSUE_NUMBER = (
    "get_issue",
    "update_issue",
    "lock_issue",
    "unlock_issue",
    "add_comment",
    "list_comments",
)
_NEED_PR_NUMBER = (
    "get_pr",
    "update_pr",
    "merge_pr",
    "request_review",
    "list_reviews",
    "add_pr_comment",
)
_NEED_COMMENT_ID = ("update_comment", "delete_comment")
_NEED_RELEASE_ID = ("get_release", "update_release", "delete_release")
_NEED_BRANCH = (
    "get_branch",
    "delete_branch",
    "dispatch_workflow",
)
_NEED_FILE_PATH = ("get_file_content", "create_file", "update_file", "delete_file", "list_dir")
_NEED_TITLE_BODY = (
    "create_issue",
    "update_issue",
    "create_pr",
    "update_pr",
    "create_release",
    "update_release",
)
_NEED_RAW_BODY = ("create_file", "update_file", "delete_file")
_LIST_OPS = (
    "list_issues",
    "list_comments",
    "list_prs",
    "list_reviews",
    "list_repos",
    "list_starred",
    "list_user_public_repos",
    "list_branches",
    "list_tags",
    "list_releases",
    "list_commits",
    "list_workflows",
    "list_gists",
    "list_dir",
)
_SEARCH_OPS = ("search_repos", "search_issues", "search_users", "search_code", "search_public_code")


def _cond(*ops: str) -> dict[str, Any]:
    return {"field": "operation", "value": list(ops)}


# ── property model ──────────────────────────────────────────────────


class GitHubProperties(BaseModel):
    credential: str | None = None
    operation: str = "create_issue"

    # Resource pickers — the inspector renders them as loadOptions
    # dropdowns; field validators collapse `{id, title}` to bare str.
    owner: Any = None  # accepts dict from picker or plain str
    repo: Any = None
    branch: str | None = None
    base_branch: str = "main"
    head_branch: str | None = None

    # Issue / PR / comment / release identifiers
    issue_number: int | None = None
    pr_number: int | None = None
    comment_id: int | None = None
    review_comment_body: str | None = None
    release_id: int | None = None
    workflow_run_id: int | None = None
    workflow_id_or_file: str | None = None
    tag_name: str | None = None
    sha: str | None = None
    base_sha: str | None = None
    head_sha: str | None = None

    # Public-op identifiers (string, no auth — accept owner/repo as
    # plain strings without the loadOptions picker)
    public_owner: str | None = None
    public_repo: str | None = None
    public_username: str | None = None
    public_path: str | None = None

    # Content / metadata fields
    title: str | None = None
    body: Any = None  # accept template-rendered (str / dict)
    comment_body: Any = None
    state: str = "open"
    state_filter: str = "open"
    sort: str = "created"
    direction: str = "desc"

    # Lists rendered as comma-separated for ergonomics in the inspector
    labels: str | None = None
    assignees: str | None = None
    reviewers: str | None = None
    team_reviewers: str | None = None

    # File ops
    file_path: str | None = None
    file_content: Any = None  # str or {raw: bytes / base64}
    file_encoding: str = "utf-8"
    commit_message: str | None = None

    # Release flags
    draft: bool = False
    prerelease: bool = False

    # Repo create
    new_repo_name: str | None = None
    new_repo_description: str | None = None
    new_repo_private: bool = False
    new_repo_auto_init: bool = True

    # Merge options
    merge_method: str = "merge"  # merge | squash | rebase

    # Workflow dispatch
    workflow_inputs: Any = None  # JSON

    # Gist
    gist_id: str | None = None
    gist_description: str | None = None
    gist_files: Any = None  # {filename: content_str}
    gist_public: bool = False

    # Search
    query: str | None = None

    # Pagination
    per_page: int = 30
    page: int = 1

    @field_validator("owner", "repo", mode="before")
    @classmethod
    def _coerce_picker(cls, value: Any) -> str | None:
        return coerce_owner_repo(value)


# ── node class ──────────────────────────────────────────────────────


class GitHubNode(BaseNode[GitHubProperties]):
    @classmethod
    def get_properties_model(cls) -> type[GitHubProperties]:
        return GitHubProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.github",
            name="GitHub",
            category="integration",
            description=(
                "Manage GitHub issues, pull requests, repos, branches, files, "
                "releases, workflows, gists, and search across the public REST API."
            ),
            icon="github",
            color="#ffffff",
            credential_type=["github_oauth", "github_pat"],
            properties=_PROPERTIES,
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "id", "type": "number"},
                {"label": "number", "type": "number"},
                {"label": "title", "type": "string"},
                {"label": "body", "type": "string"},
                {"label": "state", "type": "string"},
                {"label": "html_url", "type": "string"},
                {"label": "author", "type": "object"},
                {"label": "items", "type": "array"},
            ],
            allow_error=True,
        )

    def _get_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        op = self.props.operation
        handler = _HANDLERS.get(op)
        if handler is None:
            return NodeResult(success=False, error=f"Unknown operation: {op}")

        # Public ops bypass auth — they hit unauthenticated endpoints
        # at api.github.com (60 req/hr per IP, plenty for low-volume
        # lookups). Anything else demands a connected GitHub account.
        token: str | None = None
        if op not in _PUBLIC_OPS:
            token = self._get_token()
            if not token:
                return NodeResult(
                    success=False,
                    error="GitHub credential required for this operation.",
                )

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                return await handler(self, client, token)
        except GitHubError as exc:
            return NodeResult(
                success=False,
                error=f"GitHub API error {exc.status}: {exc.message}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GitHubNode {op} failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))


# ── property definitions (large; declared at module scope) ──────────

_OP_OPTIONS = [
    # Public — no auth
    {"label": "Get Public Repo (no auth)", "value": "get_public_repo"},
    {"label": "Get Public File (no auth)", "value": "get_public_file"},
    {"label": "List User Public Repos (no auth)", "value": "list_user_public_repos"},
    {"label": "Search Public Code (no auth)", "value": "search_public_code"},
    # Issues
    {"label": "Create Issue", "value": "create_issue"},
    {"label": "Get Issue", "value": "get_issue"},
    {"label": "Update Issue", "value": "update_issue"},
    {"label": "List Issues", "value": "list_issues"},
    {"label": "Lock Issue", "value": "lock_issue"},
    {"label": "Unlock Issue", "value": "unlock_issue"},
    {"label": "Search Issues", "value": "search_issues"},
    # Comments
    {"label": "Add Comment", "value": "add_comment"},
    {"label": "List Comments", "value": "list_comments"},
    {"label": "Update Comment", "value": "update_comment"},
    {"label": "Delete Comment", "value": "delete_comment"},
    # Pull requests
    {"label": "Create Pull Request", "value": "create_pr"},
    {"label": "Get Pull Request", "value": "get_pr"},
    {"label": "Update Pull Request", "value": "update_pr"},
    {"label": "List Pull Requests", "value": "list_prs"},
    {"label": "Merge Pull Request", "value": "merge_pr"},
    {"label": "Add PR Comment", "value": "add_pr_comment"},
    {"label": "Request Review", "value": "request_review"},
    {"label": "List Reviews", "value": "list_reviews"},
    # Repos
    {"label": "Get Repository", "value": "get_repo"},
    {"label": "List My Repositories", "value": "list_repos"},
    {"label": "Create Repository", "value": "create_repo"},
    {"label": "Delete Repository", "value": "delete_repo"},
    {"label": "Star Repository", "value": "star_repo"},
    {"label": "Unstar Repository", "value": "unstar_repo"},
    {"label": "List Starred", "value": "list_starred"},
    # Branches
    {"label": "Create Branch", "value": "create_branch"},
    {"label": "Get Branch", "value": "get_branch"},
    {"label": "List Branches", "value": "list_branches"},
    {"label": "Delete Branch", "value": "delete_branch"},
    {"label": "Get Default Branch", "value": "get_default_branch"},
    # Files
    {"label": "Get File Content", "value": "get_file_content"},
    {"label": "Create File", "value": "create_file"},
    {"label": "Update File", "value": "update_file"},
    {"label": "Delete File", "value": "delete_file"},
    {"label": "List Directory", "value": "list_dir"},
    # Releases
    {"label": "Create Release", "value": "create_release"},
    {"label": "Get Release", "value": "get_release"},
    {"label": "List Releases", "value": "list_releases"},
    {"label": "Update Release", "value": "update_release"},
    {"label": "Delete Release", "value": "delete_release"},
    # Tags
    {"label": "Create Tag", "value": "create_tag"},
    {"label": "List Tags", "value": "list_tags"},
    # Commits
    {"label": "Get Commit", "value": "get_commit"},
    {"label": "List Commits", "value": "list_commits"},
    {"label": "Compare Commits", "value": "compare_commits"},
    # Workflows
    {"label": "List Workflows", "value": "list_workflows"},
    {"label": "Get Workflow Run", "value": "get_workflow_run"},
    {"label": "Dispatch Workflow", "value": "dispatch_workflow"},
    {"label": "Cancel Workflow Run", "value": "cancel_workflow_run"},
    {"label": "Rerun Workflow", "value": "rerun_workflow"},
    # Users
    {"label": "Get Authenticated User", "value": "get_authenticated_user"},
    {"label": "Get User by Username", "value": "get_user"},
    # Gists
    {"label": "Create Gist", "value": "create_gist"},
    {"label": "Get Gist", "value": "get_gist"},
    {"label": "List My Gists", "value": "list_gists"},
    {"label": "Update Gist", "value": "update_gist"},
    {"label": "Delete Gist", "value": "delete_gist"},
    # Search (auth)
    {"label": "Search Repos", "value": "search_repos"},
    {"label": "Search Users", "value": "search_users"},
]


_PROPERTIES: list[dict[str, Any]] = [
    {
        "name": "credential",
        "label": "GitHub Account",
        "type": "credential",
        "credentialType": ["github_oauth", "github_pat"],
        "required": True,
        # Hide the credential picker on public-read operations.
        # Mirrors `gyt_node.py:_PUBLIC_OPS`.
        "condition": {
            "field": "operation",
            "operator": "notIn",
            "value": list(_PUBLIC_OPS),
        },
    },
    {
        "name": "operation",
        "label": "Operation",
        "type": "options",
        "default": "create_issue",
        "options": _OP_OPTIONS,
    },
    # ── owner / repo picker (authenticated ops) ─────────────────────
    {
        "name": "owner",
        "label": "Owner",
        "type": "string",
        "required": True,
        "placeholder": "octocat",
        "condition": _cond(*_NEED_OWNER_REPO_OPS),
    },
    {
        "name": "repo",
        "label": "Repository",
        "type": "string",
        "required": True,
        "placeholder": "hello-world",
        "loadOptions": "/integrations/github/repos",
        "loadOptionsDependsOn": ["credential", "owner"],
        "condition": _cond(*_NEED_OWNER_REPO_OPS),
    },
    # ── public-op owner / repo / username (no picker, no auth) ──────
    {
        "name": "public_owner",
        "label": "Owner",
        "type": "string",
        "required": True,
        "placeholder": "octocat",
        "condition": _cond("get_public_repo", "get_public_file"),
        "description": "GitHub username or org. Public read — no sign-in needed.",
    },
    {
        "name": "public_repo",
        "label": "Repository",
        "type": "string",
        "required": True,
        "placeholder": "hello-world",
        "condition": _cond("get_public_repo", "get_public_file"),
    },
    {
        "name": "public_username",
        "label": "Username",
        "type": "string",
        "required": True,
        "placeholder": "octocat",
        "condition": _cond("list_user_public_repos"),
    },
    {
        "name": "public_path",
        "label": "File Path",
        "type": "string",
        "required": True,
        "placeholder": "README.md",
        "condition": _cond("get_public_file"),
    },
    # ── branch picker ───────────────────────────────────────────────
    {
        "name": "branch",
        "label": "Branch",
        "type": "string",
        "loadOptions": "/integrations/github/branches",
        "loadOptionsDependsOn": ["credential", "owner", "repo"],
        "condition": _cond(*_NEED_BRANCH),
    },
    {
        "name": "base_branch",
        "label": "Base Branch",
        "type": "string",
        "default": "main",
        "placeholder": "main",
        "loadOptions": "/integrations/github/branches",
        "loadOptionsDependsOn": ["credential", "owner", "repo"],
        "condition": _cond(
            "create_pr",
            "create_branch",
            "compare_commits",
            "create_file",
            "update_file",
            "delete_file",
            "get_file_content",
            "list_dir",
            "list_commits",
        ),
    },
    {
        "name": "head_branch",
        "label": "Head Branch (source)",
        "type": "string",
        "required": True,
        "loadOptions": "/integrations/github/branches",
        "loadOptionsDependsOn": ["credential", "owner", "repo"],
        "condition": _cond("create_pr", "create_branch", "compare_commits"),
    },
    # ── issue / pr / comment / release / sha numerics ───────────────
    {
        "name": "issue_number",
        "label": "Issue Number",
        "type": "number",
        "required": True,
        "loadOptions": "/integrations/github/issues",
        "loadOptionsDependsOn": ["credential", "owner", "repo"],
        "condition": _cond(*_NEED_ISSUE_NUMBER),
    },
    {
        "name": "pr_number",
        "label": "Pull Request Number",
        "type": "number",
        "required": True,
        "loadOptions": "/integrations/github/prs",
        "loadOptionsDependsOn": ["credential", "owner", "repo"],
        "condition": _cond(*_NEED_PR_NUMBER),
    },
    {
        "name": "comment_id",
        "label": "Comment ID",
        "type": "number",
        "required": True,
        "condition": _cond(*_NEED_COMMENT_ID),
    },
    {
        "name": "release_id",
        "label": "Release ID",
        "type": "number",
        "required": True,
        "condition": _cond(*_NEED_RELEASE_ID),
    },
    {
        "name": "workflow_id_or_file",
        "label": "Workflow ID or filename",
        "type": "string",
        "required": True,
        "placeholder": "ci.yml",
        "condition": _cond("dispatch_workflow", "rerun_workflow"),
    },
    {
        "name": "workflow_run_id",
        "label": "Workflow Run ID",
        "type": "number",
        "required": True,
        "condition": _cond("get_workflow_run", "cancel_workflow_run", "rerun_workflow"),
    },
    {
        "name": "sha",
        "label": "Commit SHA",
        "type": "string",
        "required": True,
        "condition": _cond("get_commit", "create_branch", "create_tag"),
    },
    {
        "name": "base_sha",
        "label": "Base SHA",
        "type": "string",
        "required": True,
        "condition": _cond("compare_commits"),
    },
    {
        "name": "head_sha",
        "label": "Head SHA",
        "type": "string",
        "required": True,
        "condition": _cond("compare_commits"),
    },
    {
        "name": "tag_name",
        "label": "Tag Name",
        "type": "string",
        "required": True,
        "placeholder": "v1.0.0",
        "condition": _cond("create_release", "update_release", "create_tag"),
    },
    # ── content fields ──────────────────────────────────────────────
    {
        "name": "title",
        "label": "Title",
        "type": "string",
        "condition": _cond(*_NEED_TITLE_BODY),
        "description": "Required for create ops; optional for update.",
    },
    {
        "name": "body",
        "label": "Body",
        "type": "string",
        "typeOptions": {"multiline": True, "rows": 5},
        "condition": _cond(*_NEED_TITLE_BODY),
    },
    {
        "name": "comment_body",
        "label": "Comment",
        "type": "string",
        "typeOptions": {"multiline": True, "rows": 4},
        "required": True,
        "condition": _cond("add_comment", "add_pr_comment", "update_comment"),
    },
    # ── file ops ────────────────────────────────────────────────────
    {
        "name": "file_path",
        "label": "File Path",
        "type": "string",
        "required": True,
        "placeholder": "src/index.ts",
        "condition": _cond(*_NEED_FILE_PATH),
    },
    {
        "name": "file_content",
        "label": "File Content",
        "type": "string",
        "typeOptions": {"multiline": True, "rows": 8},
        "required": True,
        "condition": _cond("create_file", "update_file"),
        "description": "Raw text. Will be base64-encoded for the GitHub API.",
    },
    {
        "name": "file_encoding",
        "label": "Content Encoding",
        "type": "options",
        "default": "utf-8",
        "options": [
            {"label": "UTF-8 (text)", "value": "utf-8"},
            {"label": "Base64 (binary)", "value": "base64"},
        ],
        "mode": "advanced",
        "condition": _cond("create_file", "update_file"),
    },
    {
        "name": "commit_message",
        "label": "Commit Message",
        "type": "string",
        "required": True,
        "condition": _cond(*_NEED_RAW_BODY),
    },
    # ── state / filter / sort ───────────────────────────────────────
    {
        "name": "state",
        "label": "State",
        "type": "options",
        "default": "open",
        "options": [
            {"label": "Open", "value": "open"},
            {"label": "Closed", "value": "closed"},
        ],
        "condition": _cond("update_issue", "update_pr"),
    },
    {
        "name": "state_filter",
        "label": "Filter by State",
        "type": "options",
        "default": "open",
        "options": [
            {"label": "Open", "value": "open"},
            {"label": "Closed", "value": "closed"},
            {"label": "All", "value": "all"},
        ],
        "condition": _cond("list_issues", "list_prs"),
    },
    {
        "name": "sort",
        "label": "Sort",
        "type": "options",
        "default": "created",
        "options": [
            {"label": "Created", "value": "created"},
            {"label": "Updated", "value": "updated"},
            {"label": "Comments", "value": "comments"},
        ],
        "condition": _cond("list_issues", "list_prs"),
        "mode": "advanced",
    },
    {
        "name": "direction",
        "label": "Direction",
        "type": "options",
        "default": "desc",
        "options": [
            {"label": "Descending", "value": "desc"},
            {"label": "Ascending", "value": "asc"},
        ],
        "condition": _cond("list_issues", "list_prs"),
        "mode": "advanced",
    },
    {
        "name": "labels",
        "label": "Labels (comma-separated)",
        "type": "string",
        "placeholder": "bug, urgent",
        "condition": _cond("create_issue", "update_issue", "list_issues"),
    },
    {
        "name": "assignees",
        "label": "Assignees (comma-separated logins)",
        "type": "string",
        "placeholder": "octocat, monalisa",
        "condition": _cond("create_issue", "update_issue"),
        "mode": "advanced",
    },
    {
        "name": "reviewers",
        "label": "User Reviewers (comma-separated logins)",
        "type": "string",
        "condition": _cond("request_review"),
    },
    {
        "name": "team_reviewers",
        "label": "Team Reviewers (comma-separated slugs)",
        "type": "string",
        "condition": _cond("request_review"),
        "mode": "advanced",
    },
    # ── release flags ───────────────────────────────────────────────
    {
        "name": "draft",
        "label": "Draft",
        "type": "boolean",
        "default": False,
        "condition": _cond("create_release", "update_release"),
        "mode": "advanced",
    },
    {
        "name": "prerelease",
        "label": "Pre-release",
        "type": "boolean",
        "default": False,
        "condition": _cond("create_release", "update_release"),
        "mode": "advanced",
    },
    # ── repo create ────────────────────────────────────────────────
    {
        "name": "new_repo_name",
        "label": "Repository Name",
        "type": "string",
        "required": True,
        "placeholder": "my-new-repo",
        "condition": _cond("create_repo"),
    },
    {
        "name": "new_repo_description",
        "label": "Description",
        "type": "string",
        "condition": _cond("create_repo"),
    },
    {
        "name": "new_repo_private",
        "label": "Private",
        "type": "boolean",
        "default": False,
        "condition": _cond("create_repo"),
    },
    {
        "name": "new_repo_auto_init",
        "label": "Initialize with README",
        "type": "boolean",
        "default": True,
        "condition": _cond("create_repo"),
        "mode": "advanced",
    },
    # ── merge options ──────────────────────────────────────────────
    {
        "name": "merge_method",
        "label": "Merge Method",
        "type": "options",
        "default": "merge",
        "options": [
            {"label": "Merge commit", "value": "merge"},
            {"label": "Squash", "value": "squash"},
            {"label": "Rebase", "value": "rebase"},
        ],
        "condition": _cond("merge_pr"),
    },
    # ── workflow dispatch ──────────────────────────────────────────
    {
        "name": "workflow_inputs",
        "label": "Workflow Inputs",
        "type": "json",
        "default": {},
        "placeholder": '{"environment": "staging"}',
        "condition": _cond("dispatch_workflow"),
        "mode": "advanced",
    },
    # ── gists ──────────────────────────────────────────────────────
    {
        "name": "gist_id",
        "label": "Gist ID",
        "type": "string",
        "required": True,
        "condition": _cond("get_gist", "update_gist", "delete_gist"),
    },
    {
        "name": "gist_description",
        "label": "Description",
        "type": "string",
        "condition": _cond("create_gist", "update_gist"),
    },
    {
        "name": "gist_files",
        "label": "Files",
        "type": "json",
        "default": {},
        "placeholder": '{"hello.py": "print(\'hi\')"}',
        "required": True,
        "condition": _cond("create_gist", "update_gist"),
        "description": "Map of filename → content string.",
    },
    {
        "name": "gist_public",
        "label": "Public",
        "type": "boolean",
        "default": False,
        "condition": _cond("create_gist"),
    },
    # ── search ─────────────────────────────────────────────────────
    {
        "name": "query",
        "label": "Search Query",
        "type": "string",
        "required": True,
        "placeholder": "stars:>1000 language:python",
        "condition": _cond(*_SEARCH_OPS),
        "description": "GitHub search syntax (see docs.github.com/en/search-github/).",
    },
    # ── pagination ─────────────────────────────────────────────────
    {
        "name": "per_page",
        "label": "Per page",
        "type": "number",
        "default": 30,
        "mode": "advanced",
        "condition": _cond(*_LIST_OPS, *_SEARCH_OPS),
    },
    {
        "name": "page",
        "label": "Page",
        "type": "number",
        "default": 1,
        "mode": "advanced",
        "condition": _cond(*_LIST_OPS, *_SEARCH_OPS),
    },
]


# ── handlers ────────────────────────────────────────────────────────


def _require(name: str, value: Any) -> NodeResult | str | int:
    if value in (None, "", 0):
        return NodeResult(success=False, error=f"`{name}` is required.")
    return value


async def _request(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    token: str | None,
    *,
    params: dict[str, Any] | None = None,
    json: Any = None,
) -> Any:
    body, _ = await github_request(client, method, path, token=token, params=params, json=json)
    return body


# ---- Issues / comments ----


async def _create_issue(
    node: GitHubNode, client: httpx.AsyncClient, token: str | None
) -> NodeResult:
    owner = node.props.owner
    repo = node.props.repo
    if not owner or not repo or not node.props.title:
        return NodeResult(success=False, error="`owner`, `repo`, `title` are required.")
    payload: dict[str, Any] = {"title": node.props.title}
    if node.props.body:
        payload["body"] = str(node.props.body)
    labels = parse_csv(node.props.labels)
    if labels:
        payload["labels"] = labels
    assignees = parse_csv(node.props.assignees)
    if assignees:
        payload["assignees"] = assignees
    issue = await _request(client, "POST", f"/repos/{owner}/{repo}/issues", token, json=payload)
    return NodeResult(success=True, output_data=flatten_issue(issue))


async def _get_issue(node, client, token):  # type: ignore[no-untyped-def]
    if not (node.props.owner and node.props.repo and node.props.issue_number):
        return NodeResult(success=False, error="`owner`, `repo`, `issue_number` are required.")
    issue = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/issues/{node.props.issue_number}",
        token,
    )
    return NodeResult(success=True, output_data=flatten_issue(issue))


async def _update_issue(node, client, token):  # type: ignore[no-untyped-def]
    if not (node.props.owner and node.props.repo and node.props.issue_number):
        return NodeResult(success=False, error="`owner`, `repo`, `issue_number` are required.")
    payload: dict[str, Any] = {}
    if node.props.title:
        payload["title"] = node.props.title
    if node.props.body is not None:
        payload["body"] = str(node.props.body) if node.props.body else None
    if node.props.state:
        payload["state"] = node.props.state
    labels = parse_csv(node.props.labels)
    if labels or node.props.labels == "":
        payload["labels"] = labels
    if not payload:
        return NodeResult(success=False, error="At least one field must be set on update.")
    issue = await _request(
        client,
        "PATCH",
        f"/repos/{node.props.owner}/{node.props.repo}/issues/{node.props.issue_number}",
        token,
        json=payload,
    )
    return NodeResult(success=True, output_data=flatten_issue(issue))


async def _list_issues(node, client, token):  # type: ignore[no-untyped-def]
    if not (node.props.owner and node.props.repo):
        return NodeResult(success=False, error="`owner`, `repo` are required.")
    params: dict[str, Any] = {
        "state": node.props.state_filter,
        "sort": node.props.sort,
        "direction": node.props.direction,
        "per_page": clamp_per_page(node.props.per_page),
        "page": max(1, node.props.page or 1),
    }
    if node.props.labels:
        params["labels"] = node.props.labels
    raw = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/issues",
        token,
        params=params,
    )
    items = [
        flatten_issue(i) for i in raw or [] if not (isinstance(i, dict) and "pull_request" in i)
    ]
    return NodeResult(success=True, output_data={"items": items, "count": len(items)})


async def _lock_issue(node, client, token):  # type: ignore[no-untyped-def]
    await _request(
        client,
        "PUT",
        f"/repos/{node.props.owner}/{node.props.repo}/issues/{node.props.issue_number}/lock",
        token,
    )
    return NodeResult(
        success=True, output_data={"locked": True, "issue_number": node.props.issue_number}
    )


async def _unlock_issue(node, client, token):  # type: ignore[no-untyped-def]
    await _request(
        client,
        "DELETE",
        f"/repos/{node.props.owner}/{node.props.repo}/issues/{node.props.issue_number}/lock",
        token,
    )
    return NodeResult(
        success=True, output_data={"locked": False, "issue_number": node.props.issue_number}
    )


async def _add_comment(node, client, token):  # type: ignore[no-untyped-def]
    if not node.props.comment_body:
        return NodeResult(success=False, error="`comment` is required.")
    comment = await _request(
        client,
        "POST",
        f"/repos/{node.props.owner}/{node.props.repo}/issues/{node.props.issue_number}/comments",
        token,
        json={"body": str(node.props.comment_body)},
    )
    return NodeResult(success=True, output_data=flatten_comment(comment))


async def _list_comments(node, client, token):  # type: ignore[no-untyped-def]
    raw = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/issues/{node.props.issue_number}/comments",
        token,
        params={
            "per_page": clamp_per_page(node.props.per_page),
            "page": max(1, node.props.page or 1),
        },
    )
    items = [flatten_comment(c) for c in raw or []]
    return NodeResult(success=True, output_data={"items": items, "count": len(items)})


async def _update_comment(node, client, token):  # type: ignore[no-untyped-def]
    comment = await _request(
        client,
        "PATCH",
        f"/repos/{node.props.owner}/{node.props.repo}/issues/comments/{node.props.comment_id}",
        token,
        json={"body": str(node.props.comment_body)},
    )
    return NodeResult(success=True, output_data=flatten_comment(comment))


async def _delete_comment(node, client, token):  # type: ignore[no-untyped-def]
    await _request(
        client,
        "DELETE",
        f"/repos/{node.props.owner}/{node.props.repo}/issues/comments/{node.props.comment_id}",
        token,
    )
    return NodeResult(success=True, output_data={"deleted": True, "id": node.props.comment_id})


# ---- Pull requests ----


async def _create_pr(node, client, token):  # type: ignore[no-untyped-def]
    if not (node.props.title and node.props.head_branch):
        return NodeResult(success=False, error="`title` and `head_branch` are required.")
    payload: dict[str, Any] = {
        "title": node.props.title,
        "head": node.props.head_branch,
        "base": node.props.base_branch or "main",
    }
    if node.props.body:
        payload["body"] = str(node.props.body)
    pr = await _request(
        client,
        "POST",
        f"/repos/{node.props.owner}/{node.props.repo}/pulls",
        token,
        json=payload,
    )
    return NodeResult(success=True, output_data=flatten_pr(pr))


async def _get_pr(node, client, token):  # type: ignore[no-untyped-def]
    pr = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/pulls/{node.props.pr_number}",
        token,
    )
    return NodeResult(success=True, output_data=flatten_pr(pr))


async def _update_pr(node, client, token):  # type: ignore[no-untyped-def]
    payload: dict[str, Any] = {}
    if node.props.title:
        payload["title"] = node.props.title
    if node.props.body is not None:
        payload["body"] = str(node.props.body) if node.props.body else None
    if node.props.state:
        payload["state"] = node.props.state
    if not payload:
        return NodeResult(success=False, error="At least one field must be set on update.")
    pr = await _request(
        client,
        "PATCH",
        f"/repos/{node.props.owner}/{node.props.repo}/pulls/{node.props.pr_number}",
        token,
        json=payload,
    )
    return NodeResult(success=True, output_data=flatten_pr(pr))


async def _list_prs(node, client, token):  # type: ignore[no-untyped-def]
    params = {
        "state": node.props.state_filter,
        "sort": node.props.sort,
        "direction": node.props.direction,
        "per_page": clamp_per_page(node.props.per_page),
        "page": max(1, node.props.page or 1),
    }
    raw = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/pulls",
        token,
        params=params,
    )
    items = [flatten_pr(p) for p in raw or []]
    return NodeResult(success=True, output_data={"items": items, "count": len(items)})


async def _merge_pr(node, client, token):  # type: ignore[no-untyped-def]
    payload = {"merge_method": node.props.merge_method or "merge"}
    result = await _request(
        client,
        "PUT",
        f"/repos/{node.props.owner}/{node.props.repo}/pulls/{node.props.pr_number}/merge",
        token,
        json=payload,
    )
    return NodeResult(success=True, output_data=result or {"merged": True})


async def _add_pr_comment(node, client, token):  # type: ignore[no-untyped-def]
    # GitHub treats PR conversation comments as issue comments under
    # the hood — same endpoint, just use the PR number as the issue.
    comment = await _request(
        client,
        "POST",
        f"/repos/{node.props.owner}/{node.props.repo}/issues/{node.props.pr_number}/comments",
        token,
        json={"body": str(node.props.comment_body)},
    )
    return NodeResult(success=True, output_data=flatten_comment(comment))


async def _request_review(node, client, token):  # type: ignore[no-untyped-def]
    payload: dict[str, Any] = {}
    rev = parse_csv(node.props.reviewers)
    if rev:
        payload["reviewers"] = rev
    teams = parse_csv(node.props.team_reviewers)
    if teams:
        payload["team_reviewers"] = teams
    if not payload:
        return NodeResult(success=False, error="Provide `reviewers` and/or `team_reviewers`.")
    pr = await _request(
        client,
        "POST",
        f"/repos/{node.props.owner}/{node.props.repo}/pulls/{node.props.pr_number}/requested_reviewers",
        token,
        json=payload,
    )
    return NodeResult(success=True, output_data=flatten_pr(pr))


async def _list_reviews(node, client, token):  # type: ignore[no-untyped-def]
    raw = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/pulls/{node.props.pr_number}/reviews",
        token,
        params={"per_page": clamp_per_page(node.props.per_page)},
    )
    return NodeResult(success=True, output_data={"items": raw or [], "count": len(raw or [])})


# ---- Repos ----


async def _get_repo(node, client, token):  # type: ignore[no-untyped-def]
    repo = await _request(client, "GET", f"/repos/{node.props.owner}/{node.props.repo}", token)
    return NodeResult(success=True, output_data=flatten_repo(repo))


async def _list_repos(node, client, token):  # type: ignore[no-untyped-def]
    raw = await _request(
        client,
        "GET",
        "/user/repos",
        token,
        params={
            "per_page": clamp_per_page(node.props.per_page),
            "page": max(1, node.props.page or 1),
            "sort": "updated",
        },
    )
    items = [flatten_repo(r) for r in raw or []]
    return NodeResult(success=True, output_data={"items": items, "count": len(items)})


async def _create_repo(node, client, token):  # type: ignore[no-untyped-def]
    if not node.props.new_repo_name:
        return NodeResult(success=False, error="`new_repo_name` is required.")
    payload = {
        "name": node.props.new_repo_name,
        "description": node.props.new_repo_description or "",
        "private": bool(node.props.new_repo_private),
        "auto_init": bool(node.props.new_repo_auto_init),
    }
    repo = await _request(client, "POST", "/user/repos", token, json=payload)
    return NodeResult(success=True, output_data=flatten_repo(repo))


async def _delete_repo(node, client, token):  # type: ignore[no-untyped-def]
    await _request(client, "DELETE", f"/repos/{node.props.owner}/{node.props.repo}", token)
    return NodeResult(
        success=True,
        output_data={"deleted": True, "full_name": f"{node.props.owner}/{node.props.repo}"},
    )


async def _star_repo(node, client, token):  # type: ignore[no-untyped-def]
    await _request(client, "PUT", f"/user/starred/{node.props.owner}/{node.props.repo}", token)
    return NodeResult(success=True, output_data={"starred": True})


async def _unstar_repo(node, client, token):  # type: ignore[no-untyped-def]
    await _request(client, "DELETE", f"/user/starred/{node.props.owner}/{node.props.repo}", token)
    return NodeResult(success=True, output_data={"starred": False})


async def _list_starred(node, client, token):  # type: ignore[no-untyped-def]
    raw = await _request(
        client,
        "GET",
        "/user/starred",
        token,
        params={
            "per_page": clamp_per_page(node.props.per_page),
            "page": max(1, node.props.page or 1),
        },
    )
    items = [flatten_repo(r) for r in raw or []]
    return NodeResult(success=True, output_data={"items": items, "count": len(items)})


# ---- Branches ----


async def _create_branch(node, client, token):  # type: ignore[no-untyped-def]
    # Create branch = create a ref pointing at a source SHA. The
    # source SHA is either provided directly (`sha`) or derived from
    # the head_branch's current tip.
    sha = node.props.sha
    if not sha and node.props.head_branch:
        ref = await _request(
            client,
            "GET",
            f"/repos/{node.props.owner}/{node.props.repo}/git/ref/heads/{node.props.head_branch}",
            token,
        )
        sha = (ref or {}).get("object", {}).get("sha")
    if not sha:
        return NodeResult(
            success=False, error="Provide `sha` OR `head_branch` so we know what to branch from."
        )
    if not node.props.branch:
        return NodeResult(success=False, error="`branch` (new branch name) is required.")
    payload = {"ref": f"refs/heads/{node.props.branch}", "sha": sha}
    result = await _request(
        client,
        "POST",
        f"/repos/{node.props.owner}/{node.props.repo}/git/refs",
        token,
        json=payload,
    )
    return NodeResult(success=True, output_data=result or {"created": True})


async def _get_branch(node, client, token):  # type: ignore[no-untyped-def]
    branch = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/branches/{node.props.branch}",
        token,
    )
    return NodeResult(success=True, output_data=flatten_branch(branch))


async def _list_branches(node, client, token):  # type: ignore[no-untyped-def]
    raw = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/branches",
        token,
        params={
            "per_page": clamp_per_page(node.props.per_page),
            "page": max(1, node.props.page or 1),
        },
    )
    items = [flatten_branch(b) for b in raw or []]
    return NodeResult(success=True, output_data={"items": items, "count": len(items)})


async def _delete_branch(node, client, token):  # type: ignore[no-untyped-def]
    await _request(
        client,
        "DELETE",
        f"/repos/{node.props.owner}/{node.props.repo}/git/refs/heads/{node.props.branch}",
        token,
    )
    return NodeResult(success=True, output_data={"deleted": True, "branch": node.props.branch})


async def _get_default_branch(node, client, token):  # type: ignore[no-untyped-def]
    repo = await _request(client, "GET", f"/repos/{node.props.owner}/{node.props.repo}", token)
    return NodeResult(
        success=True, output_data={"default_branch": (repo or {}).get("default_branch")}
    )


# ---- Files ----


async def _get_file_content(node, client, token):  # type: ignore[no-untyped-def]
    params = {"ref": node.props.base_branch} if node.props.base_branch else None
    raw = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/contents/{node.props.file_path}",
        token,
        params=params,
    )
    if isinstance(raw, dict) and raw.get("type") == "file":
        try:
            content = base64.b64decode(raw.get("content", "")).decode("utf-8")
        except Exception:  # noqa: BLE001
            content = None
        return NodeResult(
            success=True,
            output_data={
                "path": raw.get("path"),
                "sha": raw.get("sha"),
                "size": raw.get("size"),
                "encoding": raw.get("encoding"),
                "content": content,
                "html_url": raw.get("html_url"),
                "download_url": raw.get("download_url"),
            },
        )
    return NodeResult(success=False, error="Path does not point to a file.")


async def _create_or_update_file(node, client, token, *, updating: bool) -> NodeResult:
    if not (node.props.file_path and node.props.commit_message):
        return NodeResult(success=False, error="`file_path` and `commit_message` are required.")
    raw_content = node.props.file_content or ""
    if node.props.file_encoding == "base64":
        encoded = str(raw_content)
    else:
        encoded = base64.b64encode(str(raw_content).encode("utf-8")).decode("ascii")
    payload: dict[str, Any] = {
        "message": node.props.commit_message,
        "content": encoded,
    }
    if node.props.base_branch:
        payload["branch"] = node.props.base_branch
    if updating:
        # SHA of the existing blob is required for updates.
        params = {"ref": node.props.base_branch} if node.props.base_branch else None
        existing = await _request(
            client,
            "GET",
            f"/repos/{node.props.owner}/{node.props.repo}/contents/{node.props.file_path}",
            token,
            params=params,
        )
        if isinstance(existing, dict) and existing.get("sha"):
            payload["sha"] = existing["sha"]
    result = await _request(
        client,
        "PUT",
        f"/repos/{node.props.owner}/{node.props.repo}/contents/{node.props.file_path}",
        token,
        json=payload,
    )
    return NodeResult(success=True, output_data=result)


async def _create_file(node, client, token):  # type: ignore[no-untyped-def]
    return await _create_or_update_file(node, client, token, updating=False)


async def _update_file(node, client, token):  # type: ignore[no-untyped-def]
    return await _create_or_update_file(node, client, token, updating=True)


async def _delete_file(node, client, token):  # type: ignore[no-untyped-def]
    if not (node.props.file_path and node.props.commit_message):
        return NodeResult(success=False, error="`file_path` and `commit_message` are required.")
    params = {"ref": node.props.base_branch} if node.props.base_branch else None
    existing = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/contents/{node.props.file_path}",
        token,
        params=params,
    )
    sha = (existing or {}).get("sha") if isinstance(existing, dict) else None
    if not sha:
        return NodeResult(success=False, error="File not found at that path.")
    payload: dict[str, Any] = {"message": node.props.commit_message, "sha": sha}
    if node.props.base_branch:
        payload["branch"] = node.props.base_branch
    await _request(
        client,
        "DELETE",
        f"/repos/{node.props.owner}/{node.props.repo}/contents/{node.props.file_path}",
        token,
        json=payload,
    )
    return NodeResult(success=True, output_data={"deleted": True, "path": node.props.file_path})


async def _list_dir(node, client, token):  # type: ignore[no-untyped-def]
    params = {"ref": node.props.base_branch} if node.props.base_branch else None
    raw = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/contents/{node.props.file_path or ''}",
        token,
        params=params,
    )
    items = raw if isinstance(raw, list) else [raw]
    items = [
        {
            "name": i.get("name"),
            "path": i.get("path"),
            "type": i.get("type"),
            "size": i.get("size"),
            "sha": i.get("sha"),
            "html_url": i.get("html_url"),
            "download_url": i.get("download_url"),
        }
        for i in items
        if isinstance(i, dict)
    ]
    return NodeResult(success=True, output_data={"items": items, "count": len(items)})


# ---- Releases ----


async def _create_release(node, client, token):  # type: ignore[no-untyped-def]
    if not node.props.tag_name:
        return NodeResult(success=False, error="`tag_name` is required.")
    payload: dict[str, Any] = {
        "tag_name": node.props.tag_name,
        "name": node.props.title or node.props.tag_name,
        "draft": bool(node.props.draft),
        "prerelease": bool(node.props.prerelease),
    }
    if node.props.body:
        payload["body"] = str(node.props.body)
    release = await _request(
        client,
        "POST",
        f"/repos/{node.props.owner}/{node.props.repo}/releases",
        token,
        json=payload,
    )
    return NodeResult(success=True, output_data=flatten_release(release))


async def _get_release(node, client, token):  # type: ignore[no-untyped-def]
    release = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/releases/{node.props.release_id}",
        token,
    )
    return NodeResult(success=True, output_data=flatten_release(release))


async def _list_releases(node, client, token):  # type: ignore[no-untyped-def]
    raw = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/releases",
        token,
        params={
            "per_page": clamp_per_page(node.props.per_page),
            "page": max(1, node.props.page or 1),
        },
    )
    items = [flatten_release(r) for r in raw or []]
    return NodeResult(success=True, output_data={"items": items, "count": len(items)})


async def _update_release(node, client, token):  # type: ignore[no-untyped-def]
    payload: dict[str, Any] = {}
    if node.props.tag_name:
        payload["tag_name"] = node.props.tag_name
    if node.props.title:
        payload["name"] = node.props.title
    if node.props.body is not None:
        payload["body"] = str(node.props.body) if node.props.body else None
    payload["draft"] = bool(node.props.draft)
    payload["prerelease"] = bool(node.props.prerelease)
    release = await _request(
        client,
        "PATCH",
        f"/repos/{node.props.owner}/{node.props.repo}/releases/{node.props.release_id}",
        token,
        json=payload,
    )
    return NodeResult(success=True, output_data=flatten_release(release))


async def _delete_release(node, client, token):  # type: ignore[no-untyped-def]
    await _request(
        client,
        "DELETE",
        f"/repos/{node.props.owner}/{node.props.repo}/releases/{node.props.release_id}",
        token,
    )
    return NodeResult(success=True, output_data={"deleted": True, "id": node.props.release_id})


# ---- Tags ----


async def _create_tag(node, client, token):  # type: ignore[no-untyped-def]
    if not (node.props.tag_name and node.props.sha):
        return NodeResult(success=False, error="`tag_name` and `sha` are required.")
    # Lightweight tag = ref `refs/tags/<name>` pointing at the sha.
    payload = {"ref": f"refs/tags/{node.props.tag_name}", "sha": node.props.sha}
    result = await _request(
        client,
        "POST",
        f"/repos/{node.props.owner}/{node.props.repo}/git/refs",
        token,
        json=payload,
    )
    return NodeResult(success=True, output_data=result or {"created": True})


async def _list_tags(node, client, token):  # type: ignore[no-untyped-def]
    raw = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/tags",
        token,
        params={
            "per_page": clamp_per_page(node.props.per_page),
            "page": max(1, node.props.page or 1),
        },
    )
    return NodeResult(success=True, output_data={"items": raw or [], "count": len(raw or [])})


# ---- Commits ----


async def _get_commit(node, client, token):  # type: ignore[no-untyped-def]
    commit = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/commits/{node.props.sha}",
        token,
    )
    return NodeResult(success=True, output_data=flatten_commit(commit))


async def _list_commits(node, client, token):  # type: ignore[no-untyped-def]
    params: dict[str, Any] = {
        "per_page": clamp_per_page(node.props.per_page),
        "page": max(1, node.props.page or 1),
    }
    if node.props.base_branch:
        params["sha"] = node.props.base_branch
    if node.props.file_path:
        params["path"] = node.props.file_path
    raw = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/commits",
        token,
        params=params,
    )
    items = [flatten_commit(c) for c in raw or []]
    return NodeResult(success=True, output_data={"items": items, "count": len(items)})


async def _compare_commits(node, client, token):  # type: ignore[no-untyped-def]
    if not (node.props.base_sha and node.props.head_sha):
        return NodeResult(success=False, error="`base_sha` and `head_sha` are required.")
    cmp = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/compare/{node.props.base_sha}...{node.props.head_sha}",
        token,
    )
    return NodeResult(
        success=True,
        output_data={
            "status": (cmp or {}).get("status"),
            "ahead_by": (cmp or {}).get("ahead_by"),
            "behind_by": (cmp or {}).get("behind_by"),
            "total_commits": (cmp or {}).get("total_commits"),
            "commits": [flatten_commit(c) for c in (cmp or {}).get("commits") or []],
            "files": [
                {
                    "filename": f.get("filename"),
                    "status": f.get("status"),
                    "additions": f.get("additions"),
                    "deletions": f.get("deletions"),
                }
                for f in (cmp or {}).get("files") or []
                if isinstance(f, dict)
            ],
            "html_url": (cmp or {}).get("html_url"),
        },
    )


# ---- Workflows ----


async def _list_workflows(node, client, token):  # type: ignore[no-untyped-def]
    raw = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/actions/workflows",
        token,
        params={
            "per_page": clamp_per_page(node.props.per_page),
            "page": max(1, node.props.page or 1),
        },
    )
    workflows = (raw or {}).get("workflows") or []
    return NodeResult(success=True, output_data={"items": workflows, "count": len(workflows)})


async def _get_workflow_run(node, client, token):  # type: ignore[no-untyped-def]
    run = await _request(
        client,
        "GET",
        f"/repos/{node.props.owner}/{node.props.repo}/actions/runs/{node.props.workflow_run_id}",
        token,
    )
    return NodeResult(success=True, output_data=flatten_workflow_run(run))


async def _dispatch_workflow(node, client, token):  # type: ignore[no-untyped-def]
    if not (node.props.workflow_id_or_file and node.props.branch):
        return NodeResult(success=False, error="`workflow_id_or_file` and `branch` are required.")
    payload: dict[str, Any] = {"ref": node.props.branch}
    if isinstance(node.props.workflow_inputs, dict) and node.props.workflow_inputs:
        payload["inputs"] = node.props.workflow_inputs
    await _request(
        client,
        "POST",
        f"/repos/{node.props.owner}/{node.props.repo}/actions/workflows/{node.props.workflow_id_or_file}/dispatches",
        token,
        json=payload,
    )
    return NodeResult(success=True, output_data={"dispatched": True, "ref": node.props.branch})


async def _cancel_workflow_run(node, client, token):  # type: ignore[no-untyped-def]
    await _request(
        client,
        "POST",
        f"/repos/{node.props.owner}/{node.props.repo}/actions/runs/{node.props.workflow_run_id}/cancel",
        token,
    )
    return NodeResult(
        success=True, output_data={"cancelled": True, "run_id": node.props.workflow_run_id}
    )


async def _rerun_workflow(node, client, token):  # type: ignore[no-untyped-def]
    await _request(
        client,
        "POST",
        f"/repos/{node.props.owner}/{node.props.repo}/actions/runs/{node.props.workflow_run_id}/rerun",
        token,
    )
    return NodeResult(
        success=True, output_data={"rerun": True, "run_id": node.props.workflow_run_id}
    )


# ---- Users ----


async def _get_authenticated_user(node, client, token):  # type: ignore[no-untyped-def]
    user = await _request(client, "GET", "/user", token)
    return NodeResult(success=True, output_data=user)


async def _get_user(node, client, token):  # type: ignore[no-untyped-def]
    if not node.props.public_username:
        return NodeResult(success=False, error="`username` is required.")
    user = await _request(client, "GET", f"/users/{node.props.public_username}", token)
    return NodeResult(success=True, output_data=user)


# ---- Gists ----


def _gist_files_payload(files: Any) -> dict[str, Any]:
    if not isinstance(files, dict):
        return {}
    return {
        name: {"content": str(content)}
        for name, content in files.items()
        if isinstance(name, str) and content is not None
    }


async def _create_gist(node, client, token):  # type: ignore[no-untyped-def]
    files = _gist_files_payload(node.props.gist_files)
    if not files:
        return NodeResult(success=False, error="`gist_files` must contain at least one file.")
    payload = {
        "description": node.props.gist_description or "",
        "public": bool(node.props.gist_public),
        "files": files,
    }
    gist = await _request(client, "POST", "/gists", token, json=payload)
    return NodeResult(success=True, output_data=flatten_gist(gist))


async def _get_gist(node, client, token):  # type: ignore[no-untyped-def]
    gist = await _request(client, "GET", f"/gists/{node.props.gist_id}", token)
    return NodeResult(success=True, output_data=flatten_gist(gist))


async def _list_gists(node, client, token):  # type: ignore[no-untyped-def]
    raw = await _request(
        client,
        "GET",
        "/gists",
        token,
        params={
            "per_page": clamp_per_page(node.props.per_page),
            "page": max(1, node.props.page or 1),
        },
    )
    items = [flatten_gist(g) for g in raw or []]
    return NodeResult(success=True, output_data={"items": items, "count": len(items)})


async def _update_gist(node, client, token):  # type: ignore[no-untyped-def]
    payload: dict[str, Any] = {}
    if node.props.gist_description is not None:
        payload["description"] = node.props.gist_description
    files = _gist_files_payload(node.props.gist_files)
    if files:
        payload["files"] = files
    if not payload:
        return NodeResult(success=False, error="At least one field must be set on update.")
    gist = await _request(client, "PATCH", f"/gists/{node.props.gist_id}", token, json=payload)
    return NodeResult(success=True, output_data=flatten_gist(gist))


async def _delete_gist(node, client, token):  # type: ignore[no-untyped-def]
    await _request(client, "DELETE", f"/gists/{node.props.gist_id}", token)
    return NodeResult(success=True, output_data={"deleted": True, "id": node.props.gist_id})


# ---- Search ----


def _search_params(node: GitHubNode) -> dict[str, Any]:
    return {
        "q": node.props.query or "",
        "per_page": clamp_per_page(node.props.per_page),
        "page": max(1, node.props.page or 1),
    }


async def _search_repos(node, client, token):  # type: ignore[no-untyped-def]
    raw = await _request(client, "GET", "/search/repositories", token, params=_search_params(node))
    items = [flatten_repo(r) for r in (raw or {}).get("items") or []]
    return NodeResult(
        success=True,
        output_data={
            "items": items,
            "total_count": (raw or {}).get("total_count"),
            "count": len(items),
        },
    )


async def _search_issues(node, client, token):  # type: ignore[no-untyped-def]
    raw = await _request(client, "GET", "/search/issues", token, params=_search_params(node))
    items = [flatten_issue(i) for i in (raw or {}).get("items") or []]
    return NodeResult(
        success=True,
        output_data={
            "items": items,
            "total_count": (raw or {}).get("total_count"),
            "count": len(items),
        },
    )


async def _search_users(node, client, token):  # type: ignore[no-untyped-def]
    raw = await _request(client, "GET", "/search/users", token, params=_search_params(node))
    return NodeResult(
        success=True,
        output_data={
            "items": (raw or {}).get("items") or [],
            "total_count": (raw or {}).get("total_count"),
        },
    )


async def _search_code(node, client, token):  # type: ignore[no-untyped-def]
    raw = await _request(client, "GET", "/search/code", token, params=_search_params(node))
    return NodeResult(
        success=True,
        output_data={
            "items": (raw or {}).get("items") or [],
            "total_count": (raw or {}).get("total_count"),
        },
    )


# ---- Public (no auth) ----


async def _get_public_repo(node, client, token):  # type: ignore[no-untyped-def]
    if not (node.props.public_owner and node.props.public_repo):
        return NodeResult(success=False, error="`owner` and `repo` are required.")
    repo = await _request(
        client,
        "GET",
        f"/repos/{node.props.public_owner}/{node.props.public_repo}",
        token,
    )
    return NodeResult(success=True, output_data=flatten_repo(repo))


async def _get_public_file(node, client, token):  # type: ignore[no-untyped-def]
    if not (node.props.public_owner and node.props.public_repo and node.props.public_path):
        return NodeResult(success=False, error="`owner`, `repo`, `path` are required.")
    raw = await _request(
        client,
        "GET",
        f"/repos/{node.props.public_owner}/{node.props.public_repo}/contents/{node.props.public_path}",
        token,
    )
    if isinstance(raw, dict) and raw.get("type") == "file":
        try:
            content = base64.b64decode(raw.get("content", "")).decode("utf-8")
        except Exception:  # noqa: BLE001
            content = None
        return NodeResult(
            success=True,
            output_data={
                "path": raw.get("path"),
                "size": raw.get("size"),
                "content": content,
                "html_url": raw.get("html_url"),
                "download_url": raw.get("download_url"),
            },
        )
    return NodeResult(success=False, error="Path does not point to a file.")


async def _list_user_public_repos(node, client, token):  # type: ignore[no-untyped-def]
    if not node.props.public_username:
        return NodeResult(success=False, error="`username` is required.")
    raw = await _request(
        client,
        "GET",
        f"/users/{node.props.public_username}/repos",
        token,
        params={
            "per_page": clamp_per_page(node.props.per_page),
            "page": max(1, node.props.page or 1),
        },
    )
    items = [flatten_repo(r) for r in raw or []]
    return NodeResult(success=True, output_data={"items": items, "count": len(items)})


async def _search_public_code(node, client, token):  # type: ignore[no-untyped-def]
    # GitHub now requires auth for /search/code, but /search/repositories
    # is fully public. For a "search public code" UX we fall back to
    # `repositories` + the `in:file` query qualifier, which works.
    raw = await _request(client, "GET", "/search/repositories", token, params=_search_params(node))
    items = [flatten_repo(r) for r in (raw or {}).get("items") or []]
    return NodeResult(
        success=True,
        output_data={
            "items": items,
            "total_count": (raw or {}).get("total_count"),
            "count": len(items),
        },
    )


# ── dispatch table ──────────────────────────────────────────────────


_HANDLERS: dict[str, Any] = {
    # Issues / comments
    "create_issue": _create_issue,
    "get_issue": _get_issue,
    "update_issue": _update_issue,
    "list_issues": _list_issues,
    "lock_issue": _lock_issue,
    "unlock_issue": _unlock_issue,
    "search_issues": _search_issues,
    "add_comment": _add_comment,
    "list_comments": _list_comments,
    "update_comment": _update_comment,
    "delete_comment": _delete_comment,
    # PRs
    "create_pr": _create_pr,
    "get_pr": _get_pr,
    "update_pr": _update_pr,
    "list_prs": _list_prs,
    "merge_pr": _merge_pr,
    "add_pr_comment": _add_pr_comment,
    "request_review": _request_review,
    "list_reviews": _list_reviews,
    # Repos
    "get_repo": _get_repo,
    "list_repos": _list_repos,
    "create_repo": _create_repo,
    "delete_repo": _delete_repo,
    "star_repo": _star_repo,
    "unstar_repo": _unstar_repo,
    "list_starred": _list_starred,
    # Branches
    "create_branch": _create_branch,
    "get_branch": _get_branch,
    "list_branches": _list_branches,
    "delete_branch": _delete_branch,
    "get_default_branch": _get_default_branch,
    # Files
    "get_file_content": _get_file_content,
    "create_file": _create_file,
    "update_file": _update_file,
    "delete_file": _delete_file,
    "list_dir": _list_dir,
    # Releases / tags / commits
    "create_release": _create_release,
    "get_release": _get_release,
    "list_releases": _list_releases,
    "update_release": _update_release,
    "delete_release": _delete_release,
    "create_tag": _create_tag,
    "list_tags": _list_tags,
    "get_commit": _get_commit,
    "list_commits": _list_commits,
    "compare_commits": _compare_commits,
    # Workflows
    "list_workflows": _list_workflows,
    "get_workflow_run": _get_workflow_run,
    "dispatch_workflow": _dispatch_workflow,
    "cancel_workflow_run": _cancel_workflow_run,
    "rerun_workflow": _rerun_workflow,
    # Users
    "get_authenticated_user": _get_authenticated_user,
    "get_user": _get_user,
    # Gists
    "create_gist": _create_gist,
    "get_gist": _get_gist,
    "list_gists": _list_gists,
    "update_gist": _update_gist,
    "delete_gist": _delete_gist,
    # Search (auth)
    "search_repos": _search_repos,
    "search_users": _search_users,
    "search_code": _search_code,
    # Public
    "get_public_repo": _get_public_repo,
    "get_public_file": _get_public_file,
    "list_user_public_repos": _list_user_public_repos,
    "search_public_code": _search_public_code,
}


# Silence unused warnings for module-private regex (kept for callers
# that may want to share the issue-number regex pattern).
_ISSUE_REGEX = re.compile(r"#(\d+)")
