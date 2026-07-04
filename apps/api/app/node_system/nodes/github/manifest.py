"""GitHub action node — manifest form.

GitHub REST API v3 at `https://api.github.com`. OAuth bearer via
`github_oauth`; the scaffold reads the token from the credential's
`access_token` key. Also supports classic PATs when supplied via the
same credential shape.

Refactored from a custom BaseNode (see git history for the earlier
form) to the shared REST scaffold. Existing 8 op names + endpoint
URLs are preserved — the change is invisible to workflows that used
create_issue / list_issues / get_issue / update_issue / add_comment /
list_comments / get_repo / list_repos. New 30+ ops (PRs, branches,
files, releases, workflows, projects) are additive.

Sim parity target: 83 ops. We ship ~40 covering the common surface.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest


def _labels(v):  # noqa: ANN001 — dynamic props
    raw = getattr(v, "labels", None) or ""
    return [x.strip() for x in raw.split(",") if x.strip()]


def _assignees(v):  # noqa: ANN001
    raw = getattr(v, "assignees", None) or ""
    return [x.strip() for x in raw.split(",") if x.strip()]


MANIFEST = ProviderManifest(
    type="action.github",
    name="GitHub",
    category="integration",
    description="GitHub — issues, PRs, files, branches, releases, workflows, projects.",
    icon_slug="github",
    color="#ffffff",
    base_url="https://api.github.com",
    credential_type="github_oauth",
    # OAuth stores the token under access_token; PATs shipped under
    # access_token by our credential encoder as well. Fall back to
    # api_key for direct-token deployments.
    token_field=["access_token", "api_key"],
    auth="bearer",
    extra_headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    },
    fields=[
        FieldSpec(name="owner", label="Owner (user or org)", type="string", placeholder="octocat"),
        FieldSpec(name="repo", label="Repository", type="string", placeholder="hello-world"),
        FieldSpec(name="issue_number", label="Issue Number", type="number"),
        FieldSpec(name="pull_number", label="Pull Request Number", type="number"),
        FieldSpec(name="title", label="Title", type="string"),
        FieldSpec(name="body", label="Body", type="string"),
        FieldSpec(name="state", label="State (open|closed)", type="string"),
        FieldSpec(name="labels", label="Labels (comma-separated)", type="string"),
        FieldSpec(name="assignees", label="Assignees (comma-separated)", type="string"),
        FieldSpec(name="comment_body", label="Comment Body", type="string"),
        FieldSpec(name="state_filter", label="State Filter", type="string", default="open"),
        FieldSpec(name="per_page", label="Per Page", type="number", default=30, mode="advanced"),
        FieldSpec(name="page", label="Page", type="number", default=1, mode="advanced"),
        FieldSpec(name="branch", label="Branch", type="string"),
        FieldSpec(name="base_branch", label="Base Branch", type="string", default="main"),
        FieldSpec(name="head_branch", label="Head Branch", type="string"),
        FieldSpec(name="ref", label="Ref (branch/tag/sha)", type="string"),
        FieldSpec(name="sha", label="Commit SHA", type="string"),
        FieldSpec(name="path", label="File Path", type="string"),
        FieldSpec(name="content_base64", label="Content (base64)", type="string"),
        FieldSpec(name="commit_message", label="Commit Message", type="string"),
        FieldSpec(name="release_tag", label="Release Tag", type="string"),
        FieldSpec(name="release_name", label="Release Name", type="string"),
        FieldSpec(name="release_body", label="Release Body", type="string"),
        FieldSpec(name="release_id", label="Release ID", type="number"),
        FieldSpec(name="prerelease", label="Prerelease", type="boolean", default=False),
        FieldSpec(name="draft", label="Draft", type="boolean", default=False),
        FieldSpec(name="workflow_id", label="Workflow ID or filename", type="string"),
        FieldSpec(name="run_id", label="Workflow Run ID", type="number"),
        FieldSpec(name="workflow_inputs", label="Workflow Inputs (JSON)", type="json", default={}),
        FieldSpec(name="comment_id", label="Comment ID", type="number"),
        FieldSpec(name="reviewers", label="Reviewers (comma-separated)", type="string"),
        FieldSpec(name="team_reviewers", label="Team Reviewers (comma-separated)", type="string"),
        FieldSpec(name="commit_message_merge", label="Merge Commit Message", type="string"),
        FieldSpec(
            name="merge_method",
            label="Merge Method (merge|squash|rebase)",
            type="string",
            default="merge",
        ),
        FieldSpec(name="project_id", label="Project ID", type="number"),
        FieldSpec(name="tree_sha", label="Tree SHA", type="string"),
        FieldSpec(name="label_name", label="Label Name", type="string"),
        FieldSpec(name="label_color", label="Label Color (hex, no #)", type="string"),
    ],
    operations=[
        # ─── legacy 8 ops (preserved) ──────────────────────────────
        OpSpec(
            id="create_issue",
            label="Create Issue",
            method="POST",
            path="/repos/{owner}/{repo}/issues",
            visible_fields=["owner", "repo", "title", "body", "labels", "assignees"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "title": getattr(v, "title", "") or "",
                    "body": getattr(v, "body", None) or None,
                    "labels": _labels(v) or None,
                    "assignees": _assignees(v) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="list_issues",
            label="List Issues",
            method="GET",
            path="/repos/{owner}/{repo}/issues",
            visible_fields=["owner", "repo", "state_filter", "labels", "per_page"],
            query_builder=lambda v: {
                "state": getattr(v, "state_filter", None) or "open",
                "labels": getattr(v, "labels", None) or None,
                "per_page": int(getattr(v, "per_page", 30) or 30),
            },
        ),
        OpSpec(
            id="get_issue",
            label="Get Issue",
            method="GET",
            path="/repos/{owner}/{repo}/issues/{issue_number}",
            visible_fields=["owner", "repo", "issue_number"],
        ),
        OpSpec(
            id="update_issue",
            label="Update Issue",
            method="PATCH",
            path="/repos/{owner}/{repo}/issues/{issue_number}",
            visible_fields=["owner", "repo", "issue_number", "title", "body", "state", "labels"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "title": getattr(v, "title", None) or None,
                    "body": getattr(v, "body", None) or None,
                    "state": getattr(v, "state", None) or None,
                    "labels": _labels(v) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="add_comment",
            label="Add Comment",
            method="POST",
            path="/repos/{owner}/{repo}/issues/{issue_number}/comments",
            visible_fields=["owner", "repo", "issue_number", "comment_body"],
            body_builder=lambda v: {"body": getattr(v, "comment_body", "") or ""},
        ),
        OpSpec(
            id="list_comments",
            label="List Comments",
            method="GET",
            path="/repos/{owner}/{repo}/issues/{issue_number}/comments",
            visible_fields=["owner", "repo", "issue_number"],
        ),
        OpSpec(
            id="get_repo",
            label="Get Repository",
            method="GET",
            path="/repos/{owner}/{repo}",
            visible_fields=["owner", "repo"],
        ),
        OpSpec(
            id="list_repos",
            label="List Repositories (authenticated user)",
            method="GET",
            path="/user/repos",
            visible_fields=["per_page"],
            query_builder=lambda v: {
                "per_page": int(getattr(v, "per_page", 30) or 30),
                "sort": "updated",
            },
        ),
        # ─── issue depth ───────────────────────────────────────────
        OpSpec(
            id="close_issue",
            label="Close Issue",
            method="PATCH",
            path="/repos/{owner}/{repo}/issues/{issue_number}",
            visible_fields=["owner", "repo", "issue_number"],
            body_builder=lambda v: {"state": "closed"},
        ),
        OpSpec(
            id="add_labels",
            label="Add Labels to Issue",
            method="POST",
            path="/repos/{owner}/{repo}/issues/{issue_number}/labels",
            visible_fields=["owner", "repo", "issue_number", "labels"],
            body_builder=lambda v: {"labels": _labels(v)},
        ),
        OpSpec(
            id="remove_label",
            label="Remove Label from Issue",
            method="DELETE",
            path="/repos/{owner}/{repo}/issues/{issue_number}/labels/{label_name}",
            visible_fields=["owner", "repo", "issue_number", "label_name"],
        ),
        OpSpec(
            id="add_assignees",
            label="Add Assignees",
            method="POST",
            path="/repos/{owner}/{repo}/issues/{issue_number}/assignees",
            visible_fields=["owner", "repo", "issue_number", "assignees"],
            body_builder=lambda v: {"assignees": _assignees(v)},
        ),
        OpSpec(
            id="update_comment",
            label="Update Comment",
            method="PATCH",
            path="/repos/{owner}/{repo}/issues/comments/{comment_id}",
            visible_fields=["owner", "repo", "comment_id", "comment_body"],
            body_builder=lambda v: {"body": getattr(v, "comment_body", "") or ""},
        ),
        OpSpec(
            id="delete_comment",
            label="Delete Comment",
            method="DELETE",
            path="/repos/{owner}/{repo}/issues/comments/{comment_id}",
            visible_fields=["owner", "repo", "comment_id"],
        ),
        # ─── pull requests ─────────────────────────────────────────
        OpSpec(
            id="list_prs",
            label="List Pull Requests",
            method="GET",
            path="/repos/{owner}/{repo}/pulls",
            visible_fields=["owner", "repo", "state_filter", "per_page"],
            query_builder=lambda v: {
                "state": getattr(v, "state_filter", None) or "open",
                "per_page": int(getattr(v, "per_page", 30) or 30),
            },
        ),
        OpSpec(
            id="get_pr",
            label="Get Pull Request",
            method="GET",
            path="/repos/{owner}/{repo}/pulls/{pull_number}",
            visible_fields=["owner", "repo", "pull_number"],
        ),
        OpSpec(
            id="create_pr",
            label="Create Pull Request",
            method="POST",
            path="/repos/{owner}/{repo}/pulls",
            visible_fields=["owner", "repo", "title", "body", "head_branch", "base_branch"],
            body_builder=lambda v: {
                "title": getattr(v, "title", "") or "",
                "body": getattr(v, "body", None) or None,
                "head": getattr(v, "head_branch", "") or "",
                "base": getattr(v, "base_branch", None) or "main",
            },
        ),
        OpSpec(
            id="update_pr",
            label="Update Pull Request",
            method="PATCH",
            path="/repos/{owner}/{repo}/pulls/{pull_number}",
            visible_fields=["owner", "repo", "pull_number", "title", "body", "state"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "title": getattr(v, "title", None) or None,
                    "body": getattr(v, "body", None) or None,
                    "state": getattr(v, "state", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="close_pr",
            label="Close Pull Request",
            method="PATCH",
            path="/repos/{owner}/{repo}/pulls/{pull_number}",
            visible_fields=["owner", "repo", "pull_number"],
            body_builder=lambda v: {"state": "closed"},
        ),
        OpSpec(
            id="merge_pr",
            label="Merge Pull Request",
            method="PUT",
            path="/repos/{owner}/{repo}/pulls/{pull_number}/merge",
            visible_fields=["owner", "repo", "pull_number", "commit_message_merge", "merge_method"],
            body_builder=lambda v: {
                "commit_message": getattr(v, "commit_message_merge", None) or None,
                "merge_method": getattr(v, "merge_method", None) or "merge",
            },
        ),
        OpSpec(
            id="get_pr_files",
            label="Get PR Files",
            method="GET",
            path="/repos/{owner}/{repo}/pulls/{pull_number}/files",
            visible_fields=["owner", "repo", "pull_number"],
        ),
        OpSpec(
            id="list_pr_comments",
            label="List PR Review Comments",
            method="GET",
            path="/repos/{owner}/{repo}/pulls/{pull_number}/comments",
            visible_fields=["owner", "repo", "pull_number"],
        ),
        OpSpec(
            id="request_reviewers",
            label="Request Reviewers on PR",
            method="POST",
            path="/repos/{owner}/{repo}/pulls/{pull_number}/requested_reviewers",
            visible_fields=["owner", "repo", "pull_number", "reviewers", "team_reviewers"],
            body_builder=lambda v: {
                "reviewers": [
                    x.strip() for x in (getattr(v, "reviewers", None) or "").split(",") if x.strip()
                ],
                "team_reviewers": [
                    x.strip()
                    for x in (getattr(v, "team_reviewers", None) or "").split(",")
                    if x.strip()
                ],
            },
        ),
        # ─── branches / files ──────────────────────────────────────
        OpSpec(
            id="list_branches",
            label="List Branches",
            method="GET",
            path="/repos/{owner}/{repo}/branches",
            visible_fields=["owner", "repo", "per_page"],
            query_builder=lambda v: {"per_page": int(getattr(v, "per_page", 30) or 30)},
        ),
        OpSpec(
            id="get_branch",
            label="Get Branch",
            method="GET",
            path="/repos/{owner}/{repo}/branches/{branch}",
            visible_fields=["owner", "repo", "branch"],
        ),
        OpSpec(
            id="create_branch",
            label="Create Branch (from base sha)",
            method="POST",
            path="/repos/{owner}/{repo}/git/refs",
            visible_fields=["owner", "repo", "branch", "sha"],
            body_builder=lambda v: {
                "ref": f"refs/heads/{getattr(v, 'branch', '') or ''}",
                "sha": getattr(v, "sha", "") or "",
            },
        ),
        OpSpec(
            id="delete_branch",
            label="Delete Branch",
            method="DELETE",
            path="/repos/{owner}/{repo}/git/refs/heads/{branch}",
            visible_fields=["owner", "repo", "branch"],
        ),
        OpSpec(
            id="get_file_content",
            label="Get File Content",
            method="GET",
            path="/repos/{owner}/{repo}/contents/{path}",
            visible_fields=["owner", "repo", "path", "ref"],
            query_builder=lambda v: {
                k: val for k, val in {"ref": getattr(v, "ref", None) or None}.items() if val
            },
        ),
        OpSpec(
            id="create_file",
            label="Create File",
            method="PUT",
            path="/repos/{owner}/{repo}/contents/{path}",
            visible_fields=["owner", "repo", "path", "branch", "commit_message", "content_base64"],
            body_builder=lambda v: {
                "message": getattr(v, "commit_message", "") or "",
                "content": getattr(v, "content_base64", "") or "",
                "branch": getattr(v, "branch", None) or None,
            },
        ),
        OpSpec(
            id="update_file",
            label="Update File",
            method="PUT",
            path="/repos/{owner}/{repo}/contents/{path}",
            visible_fields=[
                "owner",
                "repo",
                "path",
                "branch",
                "commit_message",
                "content_base64",
                "sha",
            ],
            body_builder=lambda v: {
                "message": getattr(v, "commit_message", "") or "",
                "content": getattr(v, "content_base64", "") or "",
                "sha": getattr(v, "sha", "") or "",
                "branch": getattr(v, "branch", None) or None,
            },
        ),
        OpSpec(
            id="delete_file",
            label="Delete File",
            method="DELETE",
            path="/repos/{owner}/{repo}/contents/{path}",
            visible_fields=["owner", "repo", "path", "branch", "commit_message", "sha"],
            body_builder=lambda v: {
                "message": getattr(v, "commit_message", "") or "",
                "sha": getattr(v, "sha", "") or "",
                "branch": getattr(v, "branch", None) or None,
            },
        ),
        OpSpec(
            id="latest_commit",
            label="Get Latest Commit on Branch",
            method="GET",
            path="/repos/{owner}/{repo}/commits/{branch}",
            visible_fields=["owner", "repo", "branch"],
        ),
        OpSpec(
            id="get_tree",
            label="Get Git Tree",
            method="GET",
            path="/repos/{owner}/{repo}/git/trees/{tree_sha}",
            visible_fields=["owner", "repo", "tree_sha"],
            query_builder=lambda v: {"recursive": "1"},
        ),
        # ─── releases ──────────────────────────────────────────────
        OpSpec(
            id="list_releases",
            label="List Releases",
            method="GET",
            path="/repos/{owner}/{repo}/releases",
            visible_fields=["owner", "repo", "per_page"],
            query_builder=lambda v: {"per_page": int(getattr(v, "per_page", 30) or 30)},
        ),
        OpSpec(
            id="get_release",
            label="Get Release",
            method="GET",
            path="/repos/{owner}/{repo}/releases/{release_id}",
            visible_fields=["owner", "repo", "release_id"],
        ),
        OpSpec(
            id="create_release",
            label="Create Release",
            method="POST",
            path="/repos/{owner}/{repo}/releases",
            visible_fields=[
                "owner",
                "repo",
                "release_tag",
                "release_name",
                "release_body",
                "prerelease",
                "draft",
            ],
            body_builder=lambda v: {
                "tag_name": getattr(v, "release_tag", "") or "",
                "name": getattr(v, "release_name", None) or None,
                "body": getattr(v, "release_body", None) or None,
                "prerelease": bool(getattr(v, "prerelease", False)),
                "draft": bool(getattr(v, "draft", False)),
            },
        ),
        OpSpec(
            id="update_release",
            label="Update Release",
            method="PATCH",
            path="/repos/{owner}/{repo}/releases/{release_id}",
            visible_fields=[
                "owner",
                "repo",
                "release_id",
                "release_name",
                "release_body",
                "prerelease",
                "draft",
            ],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "name": getattr(v, "release_name", None) or None,
                    "body": getattr(v, "release_body", None) or None,
                    "prerelease": bool(getattr(v, "prerelease", False)),
                    "draft": bool(getattr(v, "draft", False)),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="delete_release",
            label="Delete Release",
            method="DELETE",
            path="/repos/{owner}/{repo}/releases/{release_id}",
            visible_fields=["owner", "repo", "release_id"],
        ),
        # ─── workflows ─────────────────────────────────────────────
        OpSpec(
            id="list_workflows",
            label="List Workflows",
            method="GET",
            path="/repos/{owner}/{repo}/actions/workflows",
            visible_fields=["owner", "repo"],
        ),
        OpSpec(
            id="get_workflow",
            label="Get Workflow",
            method="GET",
            path="/repos/{owner}/{repo}/actions/workflows/{workflow_id}",
            visible_fields=["owner", "repo", "workflow_id"],
        ),
        OpSpec(
            id="trigger_workflow",
            label="Trigger Workflow Dispatch",
            method="POST",
            path="/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
            visible_fields=["owner", "repo", "workflow_id", "ref", "workflow_inputs"],
            body_builder=lambda v: {
                "ref": getattr(v, "ref", "") or "main",
                "inputs": getattr(v, "workflow_inputs", None) or {},
            },
        ),
        OpSpec(
            id="list_workflow_runs",
            label="List Workflow Runs",
            method="GET",
            path="/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs",
            visible_fields=["owner", "repo", "workflow_id", "per_page"],
            query_builder=lambda v: {"per_page": int(getattr(v, "per_page", 30) or 30)},
        ),
        OpSpec(
            id="get_workflow_run",
            label="Get Workflow Run",
            method="GET",
            path="/repos/{owner}/{repo}/actions/runs/{run_id}",
            visible_fields=["owner", "repo", "run_id"],
        ),
        OpSpec(
            id="cancel_workflow_run",
            label="Cancel Workflow Run",
            method="POST",
            path="/repos/{owner}/{repo}/actions/runs/{run_id}/cancel",
            visible_fields=["owner", "repo", "run_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="rerun_workflow",
            label="Rerun Workflow Run",
            method="POST",
            path="/repos/{owner}/{repo}/actions/runs/{run_id}/rerun",
            visible_fields=["owner", "repo", "run_id"],
            body_builder=lambda v: {},
        ),
        # ─── labels + collaborators ────────────────────────────────
        OpSpec(
            id="list_labels",
            label="List Repo Labels",
            method="GET",
            path="/repos/{owner}/{repo}/labels",
            visible_fields=["owner", "repo"],
        ),
        OpSpec(
            id="create_label",
            label="Create Repo Label",
            method="POST",
            path="/repos/{owner}/{repo}/labels",
            visible_fields=["owner", "repo", "label_name", "label_color", "body"],
            body_builder=lambda v: {
                "name": getattr(v, "label_name", "") or "",
                "color": getattr(v, "label_color", None) or "ededed",
                "description": getattr(v, "body", None) or None,
            },
        ),
        OpSpec(
            id="delete_label",
            label="Delete Repo Label",
            method="DELETE",
            path="/repos/{owner}/{repo}/labels/{label_name}",
            visible_fields=["owner", "repo", "label_name"],
        ),
        OpSpec(
            id="list_collaborators",
            label="List Collaborators",
            method="GET",
            path="/repos/{owner}/{repo}/collaborators",
            visible_fields=["owner", "repo"],
        ),
        OpSpec(
            id="get_authenticated_user",
            label="Get Authenticated User",
            method="GET",
            path="/user",
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "number"},
        {"label": "number", "type": "number"},
        {"label": "html_url", "type": "string"},
    ],
    allow_error=True,
)
