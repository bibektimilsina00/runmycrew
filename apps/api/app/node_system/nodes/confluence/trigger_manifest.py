"""Confluence polling trigger — manifest form.

Confluence Cloud REST v2 at `{base_url}/wiki/api/v2`. Basic auth
same as Jira: `{email}:{api_key}`. Custom paginate_fn since base_url
lives per-credential.

Events (poll-observable subset of sim's 22):
  - `page_created`      — known_ids on newly created pages
  - `page_updated`      — since_timestamp on version.createdAt
  - `blog_created`      — known_ids on blog posts
  - `blog_updated`      — since_timestamp on version.createdAt
  - `comment_created`   — footer comments on a target page
  - `space_created`     — known_ids on new spaces

Not in polling (need webhooks):
  page_removed / restored / moved / permissions_updated,
  attachment_created / updated / removed,
  blog_removed / restored,
  comment_removed / updated,
  label_added / removed,
  space_removed / updated,
  user_created.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    build_auth,
    register_flatten,
)
from apps.api.app.node_system.scaffolds.field_resolvers import resolve_template


def _flatten_page(item):
    version = item.get("version") or {}
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "space_id": item.get("spaceId"),
        "parent_id": item.get("parentId"),
        "status": item.get("status"),
        "author_id": item.get("authorId") or version.get("authorId"),
        "created_at": item.get("createdAt"),
        "version_number": version.get("number"),
        "version_created_at": version.get("createdAt"),
        "web_url": (item.get("_links") or {}).get("webui"),
    }


def _flatten_blog(item):
    version = item.get("version") or {}
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "space_id": item.get("spaceId"),
        "status": item.get("status"),
        "author_id": item.get("authorId") or version.get("authorId"),
        "created_at": item.get("createdAt"),
        "version_number": version.get("number"),
        "version_created_at": version.get("createdAt"),
        "web_url": (item.get("_links") or {}).get("webui"),
    }


def _flatten_comment(item):
    body = item.get("body") or {}
    version = item.get("version") or {}
    return {
        "id": item.get("id"),
        "page_id": item.get("pageId") or item.get("blogPostId"),
        "status": item.get("status"),
        "text": (body.get("storage") or {}).get("value"),
        "author_id": version.get("authorId"),
        "created_at": item.get("createdAt"),
        "version_created_at": version.get("createdAt"),
    }


def _flatten_space(item):
    return {
        "id": item.get("id"),
        "key": item.get("key"),
        "name": item.get("name"),
        "type": item.get("type"),
        "status": item.get("status"),
        "author_id": item.get("authorId"),
        "created_at": item.get("createdAt"),
        "web_url": (item.get("_links") or {}).get("webui"),
    }


register_flatten("confluence.page", _flatten_page)
register_flatten("confluence.blog", _flatten_blog)
register_flatten("confluence.comment", _flatten_comment)
register_flatten("confluence.space", _flatten_space)


async def _confluence_get(
    client: httpx.AsyncClient,
    *,
    url: str,
    token: str | None,
    email: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    auth_headers, _ = build_auth(
        token=token,
        scheme="basic",
        header_name="Authorization",
        value_template="",
        query_param="",
        basic_username=email,
    )
    headers = {**auth_headers, "Accept": "application/json"}
    resp = await client.get(url, headers=headers, params=params or None, timeout=30)
    resp.raise_for_status()
    return resp.json() or {}


async def _walk_confluence(
    client: httpx.AsyncClient,
    *,
    manifest,
    event,
    token: str | None,
    props: Any,
) -> list[dict[str, Any]]:
    """Route by event id. Base URL lives on the credential (each
    Atlassian site is a different host), so this builds it per-poll
    rather than relying on manifest.base_url."""
    cred = getattr(props, "_cred", None) or {}
    base_url = (cred.get("base_url") or "").rstrip("/")
    email = str(cred.get("email") or "")
    if not base_url or not email:
        return []
    api = f"{base_url}/wiki/api/v2"
    limit_raw = getattr(props, "max_per_poll", 25) or 25
    try:
        limit = max(1, min(int(limit_raw), 250))
    except (TypeError, ValueError):
        limit = 25

    if event.id in ("page_created", "page_updated"):
        space_id = resolve_template("{space_id}", props) or ""
        params: dict[str, Any] = {
            "limit": limit,
            "sort": "-created-date" if event.id == "page_created" else "-modified-date",
        }
        if space_id:
            params["space-id"] = space_id
        body = await _confluence_get(
            client, url=f"{api}/pages", token=token, email=email, params=params
        )
        pages = body.get("results") or []
        # Hoist version.createdAt → updated for since_timestamp diff.
        if event.id == "page_updated":
            for p in pages:
                v = p.get("version") or {}
                if v.get("createdAt"):
                    p["updated"] = v["createdAt"]
        return pages

    if event.id in ("blog_created", "blog_updated"):
        space_id = resolve_template("{space_id}", props) or ""
        params = {
            "limit": limit,
            "sort": "-created-date" if event.id == "blog_created" else "-modified-date",
        }
        if space_id:
            params["space-id"] = space_id
        body = await _confluence_get(
            client, url=f"{api}/blogposts", token=token, email=email, params=params
        )
        blogs = body.get("results") or []
        if event.id == "blog_updated":
            for b in blogs:
                v = b.get("version") or {}
                if v.get("createdAt"):
                    b["updated"] = v["createdAt"]
        return blogs

    if event.id == "comment_created":
        page_id = resolve_template("{page_id}", props) or ""
        if not page_id:
            return []
        params = {"limit": limit, "sort": "-created-date", "body-format": "storage"}
        body = await _confluence_get(
            client,
            url=f"{api}/pages/{page_id}/footer-comments",
            token=token,
            email=email,
            params=params,
        )
        return body.get("results") or []

    if event.id == "space_created":
        params = {"limit": limit, "sort": "-name"}
        body = await _confluence_get(
            client, url=f"{api}/spaces", token=token, email=email, params=params
        )
        return body.get("results") or []

    return []


MANIFEST = PollingTriggerManifest(
    type="trigger.confluence",
    name="Confluence",
    description=(
        "Poll Confluence Cloud for new / updated pages + blog posts, new "
        "comments on a target page, or new spaces."
    ),
    icon_slug="confluence",
    color="#1c1c1c",
    base_url="",
    credential_type="confluence_api_key",
    token_field=["api_key"],
    auth="basic",
    provider="confluence",
    default_poll_interval_seconds=90,
    common_fields=[
        FieldSpec(
            name="space_id",
            label="Space ID (optional; blank = all spaces)",
            type="string",
            mode="advanced",
        ),
        FieldSpec(
            name="page_id",
            label="Page ID (for comment_created event)",
            type="string",
        ),
    ],
    events=[
        PollingEvent(
            id="page_created",
            label="Page Created",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="confluence.page",
            extra_fields=["space_id"],
        ),
        PollingEvent(
            id="page_updated",
            label="Page Updated",
            list_path="",
            strategy="since_timestamp",
            timestamp_field="updated",
            flatten="confluence.page",
            extra_fields=["space_id"],
        ),
        PollingEvent(
            id="blog_created",
            label="Blog Post Created",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="confluence.blog",
            extra_fields=["space_id"],
        ),
        PollingEvent(
            id="blog_updated",
            label="Blog Post Updated",
            list_path="",
            strategy="since_timestamp",
            timestamp_field="updated",
            flatten="confluence.blog",
            extra_fields=["space_id"],
        ),
        PollingEvent(
            id="comment_created",
            label="Comment Created on Page",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="confluence.comment",
            extra_fields=["page_id"],
        ),
        PollingEvent(
            id="space_created",
            label="Space Created",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="confluence.space",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "space_id", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "created_at", "type": "string"},
        {"label": "version_number", "type": "number"},
        {"label": "text", "type": "string"},
        {"label": "web_url", "type": "string"},
    ],
    paginate_fn=_walk_confluence,
)
