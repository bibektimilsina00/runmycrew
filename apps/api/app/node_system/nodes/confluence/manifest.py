"""Confluence action node — manifest form.

Confluence Cloud REST v2 at `{base_url}/wiki/api/v2`. Basic auth
using `{email}:{api_key}` — same shape as Jira. Base URL is the
Atlassian site (yoursite.atlassian.net), stored on the credential.

10 ops cover the typical workflow:
  - list_pages / get_page / create_page / update_page / delete_page
  - list_spaces / get_space
  - list_blog_posts / create_blog_post
  - list_comments (footer comments on a page)
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

_HOST = "{base_url}/wiki/api/v2"


def _adf_wrap(text: str | None) -> dict:
    """Wrap plain text in Confluence's minimum-viable storage-format
    envelope. Confluence v2 accepts storage / atlas_doc_format / view;
    storage HTML-like is easiest for programmatic writes."""
    return {
        "representation": "storage",
        "value": f"<p>{text or ''}</p>",
    }


MANIFEST = ProviderManifest(
    type="action.confluence",
    name="Confluence",
    category="integration",
    description="Confluence Cloud — pages, spaces, blogs, comments.",
    icon_slug="confluence",
    color="#1c1c1c",
    base_url="",
    credential_type="confluence_api_key",
    token_field=["api_key"],
    auth="basic",
    auth_basic_username="{email}",
    fields=[
        FieldSpec(name="page_id", label="Page ID", type="string"),
        FieldSpec(name="space_id", label="Space ID", type="string"),
        FieldSpec(name="space_key", label="Space Key", type="string"),
        FieldSpec(name="title", label="Title", type="string"),
        FieldSpec(name="body", label="Body (HTML/storage)", type="string"),
        FieldSpec(name="parent_id", label="Parent Page ID", type="string"),
        FieldSpec(
            name="status",
            label="Status",
            type="options",
            options=[
                {"label": "Current", "value": "current"},
                {"label": "Draft", "value": "draft"},
                {"label": "Archived", "value": "archived"},
                {"label": "Trashed", "value": "trashed"},
            ],
            default="current",
            mode="advanced",
        ),
        FieldSpec(
            name="version",
            label="Version number (for updates)",
            type="number",
            mode="advanced",
        ),
        FieldSpec(name="limit", label="Limit", type="number", default=25, mode="advanced"),
        FieldSpec(name="cursor", label="Cursor", type="string", mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_pages",
            label="List Pages",
            method="GET",
            path=_HOST + "/pages",
            visible_fields=["space_id", "status", "limit"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "space-id": getattr(v, "space_id", None),
                    "status": getattr(v, "status", None),
                    "limit": int(getattr(v, "limit", 25) or 25),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_page",
            label="Get Page",
            method="GET",
            path=_HOST + "/pages/{page_id}",
            visible_fields=["page_id"],
            query_builder=lambda v: {"body-format": "storage"},
        ),
        OpSpec(
            id="create_page",
            label="Create Page",
            method="POST",
            path=_HOST + "/pages",
            visible_fields=["space_id", "title", "body", "parent_id"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "spaceId": getattr(v, "space_id", None) or "",
                    "status": getattr(v, "status", None) or "current",
                    "title": getattr(v, "title", None) or "",
                    "parentId": getattr(v, "parent_id", None),
                    "body": _adf_wrap(getattr(v, "body", None)),
                }.items()
                if val is not None and val != ""
            },
        ),
        OpSpec(
            id="update_page",
            label="Update Page",
            method="PUT",
            path=_HOST + "/pages/{page_id}",
            visible_fields=["page_id", "title", "body", "version"],
            body_builder=lambda v: {
                "id": getattr(v, "page_id", None) or "",
                "status": getattr(v, "status", None) or "current",
                "title": getattr(v, "title", None) or "",
                "body": _adf_wrap(getattr(v, "body", None)),
                "version": {"number": int(getattr(v, "version", 0) or 0) + 1},
            },
        ),
        OpSpec(
            id="delete_page",
            label="Delete Page",
            method="DELETE",
            path=_HOST + "/pages/{page_id}",
            visible_fields=["page_id"],
        ),
        OpSpec(
            id="list_spaces",
            label="List Spaces",
            method="GET",
            path=_HOST + "/spaces",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 25) or 25)},
        ),
        OpSpec(
            id="get_space",
            label="Get Space",
            method="GET",
            path=_HOST + "/spaces/{space_id}",
            visible_fields=["space_id"],
        ),
        OpSpec(
            id="list_blog_posts",
            label="List Blog Posts",
            method="GET",
            path=_HOST + "/blogposts",
            visible_fields=["space_id", "limit"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "space-id": getattr(v, "space_id", None),
                    "limit": int(getattr(v, "limit", 25) or 25),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="create_blog_post",
            label="Create Blog Post",
            method="POST",
            path=_HOST + "/blogposts",
            visible_fields=["space_id", "title", "body"],
            body_builder=lambda v: {
                "spaceId": getattr(v, "space_id", None) or "",
                "status": "current",
                "title": getattr(v, "title", None) or "",
                "body": _adf_wrap(getattr(v, "body", None)),
            },
        ),
        OpSpec(
            id="list_comments",
            label="List Comments on Page",
            method="GET",
            path=_HOST + "/pages/{page_id}/footer-comments",
            visible_fields=["page_id", "limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 25) or 25)},
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "spaceId", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "parentId", "type": "string"},
        {"label": "version", "type": "object"},
        {"label": "results", "type": "array"},
    ],
    allow_error=True,
)
