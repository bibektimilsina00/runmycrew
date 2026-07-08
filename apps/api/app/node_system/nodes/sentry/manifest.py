"""Sentry action node — manifest form.

Sentry's REST API is at `/api/0/...`. Bearer auth using a personal /
internal-integration auth token. The workflow ops we care about:

  - List issues / events for a project
  - Resolve / ignore an issue
  - Create / list releases
  - Add comments to issues
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.sentry",
    name="Sentry",
    category="integration",
    description="Manage Sentry issues, releases, and projects.",
    icon_slug="sentry",
    color="#ffffff",
    base_url="https://sentry.io/api/0",
    credential_type="sentry_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(
            name="organization_slug", label="Organization Slug", type="string", required=True
        ),
        FieldSpec(name="project_slug", label="Project Slug", type="string"),
        FieldSpec(name="issue_id", label="Issue ID", type="string"),
        FieldSpec(name="query", label="Query", type="string", mode="advanced"),
        FieldSpec(name="limit", label="Limit", type="number", default=25, mode="advanced"),
        FieldSpec(
            name="status",
            label="New status",
            type="options",
            options=[
                {"label": "Resolved", "value": "resolved"},
                {"label": "Ignored", "value": "ignored"},
                {"label": "Unresolved", "value": "unresolved"},
            ],
        ),
        FieldSpec(name="comment", label="Comment", type="string"),
        FieldSpec(name="version", label="Release Version", type="string"),
        FieldSpec(name="projects", label="Project Slugs (JSON array)", type="json"),
    ],
    operations=[
        OpSpec(
            id="list_issues",
            label="List Issues",
            method="GET",
            path="/projects/{organization_slug}/{project_slug}/issues/",
            visible_fields=["organization_slug", "project_slug", "query", "limit"],
            query_fields=["query", "limit"],
        ),
        OpSpec(
            id="get_issue",
            label="Get Issue",
            method="GET",
            path="/issues/{issue_id}/",
            visible_fields=["issue_id"],
        ),
        OpSpec(
            id="update_issue",
            label="Update Issue Status",
            method="PUT",
            path="/issues/{issue_id}/",
            visible_fields=["issue_id", "status"],
            body_fields=["status"],
        ),
        OpSpec(
            id="add_comment",
            label="Add Issue Comment",
            method="POST",
            path="/issues/{issue_id}/comments/",
            visible_fields=["issue_id", "comment"],
            body_template={"text": "{comment}"},
        ),
        OpSpec(
            id="list_releases",
            label="List Releases",
            method="GET",
            path="/organizations/{organization_slug}/releases/",
            visible_fields=["organization_slug", "limit"],
            query_fields=["limit"],
        ),
        OpSpec(
            id="create_release",
            label="Create Release",
            method="POST",
            path="/organizations/{organization_slug}/releases/",
            visible_fields=["organization_slug", "version", "projects"],
            body_fields=["version", "projects"],
        ),
        OpSpec(
            id="list_projects",
            label="List Projects",
            method="GET",
            path="/organizations/{organization_slug}/projects/",
            visible_fields=["organization_slug"],
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "level", "type": "string"},
        {"label": "items", "type": "array"},
        {"label": "shortId", "type": "string"},
        {"label": "version", "type": "string"},
    ],
    allow_error=True,
)
