"""GitLab action node — manifest form.

GitLab REST API v4 at `https://gitlab.com/api/v4` (or self-hosted).
Uses `PRIVATE-TOKEN` header for personal access tokens; the scaffold
supports this via the `header_token` scheme.

New action node — trigger + webhook already existed but no action node
was shipped before. Covers issues, MRs, pipelines, projects, groups,
files, releases, and members toward sim's 31-op parity.
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.gitlab import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)

MANIFEST = ProviderManifest(
    type="action.gitlab",
    name=NAME,
    category="integration",
    description="GitLab — issues, MRs, pipelines, projects, files, releases, members.",
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://gitlab.com/api/v4",
    credential_type="gitlab_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="PRIVATE-TOKEN",
    fields=[
        FieldSpec(
            name="project_id",
            label="Project",
            type="string",
            remote=RemoteLookup(provider="gitlab", resource="projects"),
        ),
        FieldSpec(name="group_id", label="Group ID", type="string"),
        FieldSpec(name="issue_iid", label="Issue IID", type="number"),
        FieldSpec(name="mr_iid", label="Merge Request IID", type="number"),
        FieldSpec(name="pipeline_id", label="Pipeline ID", type="number"),
        FieldSpec(name="job_id", label="Job ID", type="number"),
        FieldSpec(name="user_id", label="User ID", type="number"),
        FieldSpec(name="title", label="Title", type="string"),
        FieldSpec(name="description", label="Description", type="string"),
        FieldSpec(name="labels", label="Labels (comma-separated)", type="string"),
        FieldSpec(name="state_event", label="State Event (close|reopen)", type="string"),
        FieldSpec(name="assignee_ids", label="Assignee IDs (JSON array)", type="json", default=[]),
        FieldSpec(name="branch", label="Branch", type="string"),
        FieldSpec(name="target_branch", label="Target Branch", type="string", default="main"),
        FieldSpec(name="source_branch", label="Source Branch", type="string"),
        FieldSpec(name="commit_sha", label="Commit SHA", type="string"),
        FieldSpec(name="file_path", label="File Path", type="string"),
        FieldSpec(name="file_content", label="File Content", type="string"),
        FieldSpec(name="commit_message", label="Commit Message", type="string"),
        FieldSpec(name="ref", label="Ref (branch/tag/sha)", type="string"),
        FieldSpec(name="release_tag", label="Release Tag", type="string"),
        FieldSpec(name="release_name", label="Release Name", type="string"),
        FieldSpec(name="release_description", label="Release Description", type="string"),
        FieldSpec(
            name="access_level", label="Access Level (10/20/30/40/50)", type="number", default=30
        ),
        FieldSpec(name="username", label="Username", type="string"),
        FieldSpec(name="query", label="Search Query", type="string"),
        FieldSpec(name="per_page", label="Per Page", type="number", default=20, mode="advanced"),
    ],
    operations=[
        # ─── issues ────────────────────────────────────────────────
        OpSpec(
            id="list_issues",
            label="List Project Issues",
            method="GET",
            path="/projects/{project_id}/issues",
            visible_fields=["project_id", "labels", "per_page"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "labels": getattr(v, "labels", None) or None,
                    "per_page": int(getattr(v, "per_page", 20) or 20),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_issue",
            label="Get Issue",
            method="GET",
            path="/projects/{project_id}/issues/{issue_iid}",
            visible_fields=["project_id", "issue_iid"],
        ),
        OpSpec(
            id="create_issue",
            label="Create Issue",
            method="POST",
            path="/projects/{project_id}/issues",
            visible_fields=["project_id", "title", "description", "labels", "assignee_ids"],
            body_builder=lambda v: {
                "title": getattr(v, "title", "") or "",
                "description": getattr(v, "description", None) or None,
                "labels": getattr(v, "labels", None) or None,
                "assignee_ids": getattr(v, "assignee_ids", None) or None,
            },
        ),
        OpSpec(
            id="update_issue",
            label="Update Issue",
            method="PUT",
            path="/projects/{project_id}/issues/{issue_iid}",
            visible_fields=[
                "project_id",
                "issue_iid",
                "title",
                "description",
                "state_event",
                "labels",
            ],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "title": getattr(v, "title", None) or None,
                    "description": getattr(v, "description", None) or None,
                    "state_event": getattr(v, "state_event", None) or None,
                    "labels": getattr(v, "labels", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="delete_issue",
            label="Delete Issue",
            method="DELETE",
            path="/projects/{project_id}/issues/{issue_iid}",
            visible_fields=["project_id", "issue_iid"],
        ),
        # ─── merge requests ────────────────────────────────────────
        OpSpec(
            id="list_mrs",
            label="List Merge Requests",
            method="GET",
            path="/projects/{project_id}/merge_requests",
            visible_fields=["project_id", "per_page"],
            query_builder=lambda v: {"per_page": int(getattr(v, "per_page", 20) or 20)},
        ),
        OpSpec(
            id="get_mr",
            label="Get Merge Request",
            method="GET",
            path="/projects/{project_id}/merge_requests/{mr_iid}",
            visible_fields=["project_id", "mr_iid"],
        ),
        OpSpec(
            id="create_mr",
            label="Create Merge Request",
            method="POST",
            path="/projects/{project_id}/merge_requests",
            visible_fields=["project_id", "source_branch", "target_branch", "title", "description"],
            body_builder=lambda v: {
                "source_branch": getattr(v, "source_branch", "") or "",
                "target_branch": getattr(v, "target_branch", None) or "main",
                "title": getattr(v, "title", "") or "",
                "description": getattr(v, "description", None) or None,
            },
        ),
        OpSpec(
            id="update_mr",
            label="Update Merge Request",
            method="PUT",
            path="/projects/{project_id}/merge_requests/{mr_iid}",
            visible_fields=["project_id", "mr_iid", "title", "description", "state_event"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "title": getattr(v, "title", None) or None,
                    "description": getattr(v, "description", None) or None,
                    "state_event": getattr(v, "state_event", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="accept_mr",
            label="Accept Merge Request",
            method="PUT",
            path="/projects/{project_id}/merge_requests/{mr_iid}/merge",
            visible_fields=["project_id", "mr_iid"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="close_mr",
            label="Close Merge Request",
            method="PUT",
            path="/projects/{project_id}/merge_requests/{mr_iid}",
            visible_fields=["project_id", "mr_iid"],
            body_builder=lambda v: {"state_event": "close"},
        ),
        # ─── pipelines + jobs ──────────────────────────────────────
        OpSpec(
            id="list_pipelines",
            label="List Pipelines",
            method="GET",
            path="/projects/{project_id}/pipelines",
            visible_fields=["project_id"],
        ),
        OpSpec(
            id="get_pipeline",
            label="Get Pipeline",
            method="GET",
            path="/projects/{project_id}/pipelines/{pipeline_id}",
            visible_fields=["project_id", "pipeline_id"],
        ),
        OpSpec(
            id="create_pipeline",
            label="Create Pipeline",
            method="POST",
            path="/projects/{project_id}/pipeline",
            visible_fields=["project_id", "ref"],
            body_builder=lambda v: {"ref": getattr(v, "ref", "") or "main"},
        ),
        OpSpec(
            id="cancel_pipeline",
            label="Cancel Pipeline",
            method="POST",
            path="/projects/{project_id}/pipelines/{pipeline_id}/cancel",
            visible_fields=["project_id", "pipeline_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="retry_pipeline",
            label="Retry Pipeline",
            method="POST",
            path="/projects/{project_id}/pipelines/{pipeline_id}/retry",
            visible_fields=["project_id", "pipeline_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="list_pipeline_jobs",
            label="List Pipeline Jobs",
            method="GET",
            path="/projects/{project_id}/pipelines/{pipeline_id}/jobs",
            visible_fields=["project_id", "pipeline_id"],
        ),
        OpSpec(
            id="get_job",
            label="Get Job",
            method="GET",
            path="/projects/{project_id}/jobs/{job_id}",
            visible_fields=["project_id", "job_id"],
        ),
        # ─── projects + files ──────────────────────────────────────
        OpSpec(
            id="list_projects",
            label="List Projects",
            method="GET",
            path="/projects",
            visible_fields=["per_page"],
            query_builder=lambda v: {"per_page": int(getattr(v, "per_page", 20) or 20)},
        ),
        OpSpec(
            id="get_project",
            label="Get Project",
            method="GET",
            path="/projects/{project_id}",
            visible_fields=["project_id"],
        ),
        OpSpec(
            id="get_file",
            label="Get File Content",
            method="GET",
            path="/projects/{project_id}/repository/files/{file_path}",
            visible_fields=["project_id", "file_path", "ref"],
            query_builder=lambda v: {"ref": getattr(v, "ref", None) or "main"},
        ),
        OpSpec(
            id="create_file",
            label="Create File",
            method="POST",
            path="/projects/{project_id}/repository/files/{file_path}",
            visible_fields=["project_id", "file_path", "branch", "commit_message", "file_content"],
            body_builder=lambda v: {
                "branch": getattr(v, "branch", "") or "",
                "commit_message": getattr(v, "commit_message", "") or "",
                "content": getattr(v, "file_content", "") or "",
            },
        ),
        OpSpec(
            id="update_file",
            label="Update File",
            method="PUT",
            path="/projects/{project_id}/repository/files/{file_path}",
            visible_fields=["project_id", "file_path", "branch", "commit_message", "file_content"],
            body_builder=lambda v: {
                "branch": getattr(v, "branch", "") or "",
                "commit_message": getattr(v, "commit_message", "") or "",
                "content": getattr(v, "file_content", "") or "",
            },
        ),
        OpSpec(
            id="delete_file",
            label="Delete File",
            method="DELETE",
            path="/projects/{project_id}/repository/files/{file_path}",
            visible_fields=["project_id", "file_path", "branch", "commit_message"],
            body_builder=lambda v: {
                "branch": getattr(v, "branch", "") or "",
                "commit_message": getattr(v, "commit_message", "") or "",
            },
        ),
        # ─── releases ──────────────────────────────────────────────
        OpSpec(
            id="list_releases",
            label="List Releases",
            method="GET",
            path="/projects/{project_id}/releases",
            visible_fields=["project_id"],
        ),
        OpSpec(
            id="get_release",
            label="Get Release",
            method="GET",
            path="/projects/{project_id}/releases/{release_tag}",
            visible_fields=["project_id", "release_tag"],
        ),
        OpSpec(
            id="create_release",
            label="Create Release",
            method="POST",
            path="/projects/{project_id}/releases",
            visible_fields=[
                "project_id",
                "release_tag",
                "release_name",
                "release_description",
                "ref",
            ],
            body_builder=lambda v: {
                "tag_name": getattr(v, "release_tag", "") or "",
                "name": getattr(v, "release_name", None) or None,
                "description": getattr(v, "release_description", None) or None,
                "ref": getattr(v, "ref", None) or "main",
            },
        ),
        # ─── groups + members + users ──────────────────────────────
        OpSpec(
            id="list_groups",
            label="List Groups",
            method="GET",
            path="/groups",
        ),
        OpSpec(
            id="get_group",
            label="Get Group",
            method="GET",
            path="/groups/{group_id}",
            visible_fields=["group_id"],
        ),
        OpSpec(
            id="list_project_members",
            label="List Project Members",
            method="GET",
            path="/projects/{project_id}/members",
            visible_fields=["project_id"],
        ),
        OpSpec(
            id="add_project_member",
            label="Add Project Member",
            method="POST",
            path="/projects/{project_id}/members",
            visible_fields=["project_id", "user_id", "access_level"],
            body_builder=lambda v: {
                "user_id": int(getattr(v, "user_id", 0) or 0),
                "access_level": int(getattr(v, "access_level", 30) or 30),
            },
        ),
        OpSpec(
            id="remove_project_member",
            label="Remove Project Member",
            method="DELETE",
            path="/projects/{project_id}/members/{user_id}",
            visible_fields=["project_id", "user_id"],
        ),
        OpSpec(
            id="get_current_user",
            label="Get Current User",
            method="GET",
            path="/user",
        ),
        OpSpec(
            id="search_users",
            label="Search Users",
            method="GET",
            path="/users",
            visible_fields=["username"],
            query_builder=lambda v: {"username": getattr(v, "username", None) or None},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "number"},
        {"label": "iid", "type": "number"},
        {"label": "web_url", "type": "string"},
    ],
    allow_error=True,
)
