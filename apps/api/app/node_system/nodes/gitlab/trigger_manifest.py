"""GitLab polling trigger — manifest form.

Watches issues, merge requests, releases, commits on a GitLab
project via `known_ids` cursor diffs. Self-hosted GitLab is handled
via credential's optional `base_url` field (defaults to gitlab.com).

The scaffold's default single-page fetcher can't fold the
credential-provided base URL into `manifest.base_url` — that field
is static. Solution: manifest ships an empty base_url and each
op's list_path starts with `{base_url}` templated from the
credential dict. When credential.base_url is blank we substitute
the gitlab.com default via a paginate_fn wrapper.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)
from apps.api.app.node_system.scaffolds.field_resolvers import resolve_template


def _flatten_issue(item):
    return {
        "id": item.get("id"),
        "iid": item.get("iid"),
        "title": item.get("title"),
        "state": item.get("state"),
        "author": (item.get("author") or {}).get("username"),
        "web_url": item.get("web_url"),
        "created_at": item.get("created_at"),
    }


def _flatten_mr(item):
    return {
        "id": item.get("id"),
        "iid": item.get("iid"),
        "title": item.get("title"),
        "state": item.get("state"),
        "author": (item.get("author") or {}).get("username"),
        "web_url": item.get("web_url"),
        "source_branch": item.get("source_branch"),
        "target_branch": item.get("target_branch"),
    }


def _flatten_commit(item):
    return {
        "id": item.get("id"),
        "short_id": item.get("short_id"),
        "title": item.get("title"),
        "message": item.get("message"),
        "author_name": item.get("author_name"),
        "web_url": item.get("web_url"),
        "created_at": item.get("created_at"),
    }


def _flatten_release(item):
    return {
        "tag_name": item.get("tag_name"),
        "name": item.get("name"),
        "description": item.get("description"),
        "released_at": item.get("released_at"),
    }


register_flatten("gitlab.issue", _flatten_issue)
register_flatten("gitlab.mr", _flatten_mr)
register_flatten("gitlab.commit", _flatten_commit)
register_flatten("gitlab.release", _flatten_release)


class _GitLabView:
    """Wraps props + credential and fills in the gitlab.com default
    when credential.base_url is blank. The polling scaffold's default
    fetcher passes `props` to `resolve_template`; we hand it this
    view instead via a custom paginate_fn."""

    __slots__ = ("_props", "_cred")

    def __init__(self, props, credential):
        self._props = props
        self._cred = credential or {}

    def __getattr__(self, name):
        if name == "base_url":
            v = self._cred.get("base_url") or "https://gitlab.com"
            return v.rstrip("/")
        value = getattr(self._props, name, None)
        if value is not None:
            return value
        return self._cred.get(name)


async def _walk_gitlab(
    client: httpx.AsyncClient,
    *,
    manifest,
    event,
    token: str | None,
    props: Any,
) -> list[dict[str, Any]]:
    """GitLab paginator that fills in the base_url default before
    resolving the list_path template. Reads credential.base_url from
    the pollling_node_factory-supplied credential attribute on props
    — the factory doesn't hand credential to paginate_fn, but props
    are attribute-accessible via _PropCredView which already merges
    them.

    The trick: props here is _PropCredView (built by the factory in
    _run_poll), so `getattr(props, "base_url", None)` already reads
    the credential's base_url field. We just need to substitute a
    default when it's blank.
    """
    # `props` is already _PropCredView from the factory. Reach into
    # its private _cred to see the raw credential and fill defaults.
    cred = getattr(props, "_cred", None) or {}
    view = _GitLabView(getattr(props, "_props", props), cred)

    url = resolve_template(event.list_path, view)
    params = dict(event.list_params or {})
    resolved_params = {
        k: (resolve_template(v, view) if isinstance(v, str) else v) for k, v in params.items()
    }
    headers = {"PRIVATE-TOKEN": token or "", "Accept": "application/json"}
    resp = await client.get(url, headers=headers, params=resolved_params or None, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    return body if isinstance(body, list) else []


MANIFEST = PollingTriggerManifest(
    type="trigger.gitlab",
    name="GitLab",
    description="Poll GitLab for new issues, merge requests, releases, commits.",
    icon_slug="gitlab",
    color="#1c1c1c",
    base_url="",
    credential_type="gitlab_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="PRIVATE-TOKEN",
    provider="gitlab",
    default_poll_interval_seconds=60,
    common_fields=[
        FieldSpec(
            name="project_id",
            label="Project ID (or namespace%2Fproject URL-encoded)",
            type="string",
            required=True,
            placeholder="12345678 or my-group%2Fmy-project",
        ),
    ],
    events=[
        PollingEvent(
            id="new_issue",
            label="New Issue",
            list_path="{base_url}/api/v4/projects/{project_id}/issues",
            list_params={"state": "opened", "order_by": "created_at", "sort": "desc"},
            strategy="known_ids",
            id_field="id",
            flatten="gitlab.issue",
        ),
        PollingEvent(
            id="new_mr",
            label="New Merge Request",
            list_path="{base_url}/api/v4/projects/{project_id}/merge_requests",
            list_params={"state": "opened", "order_by": "created_at", "sort": "desc"},
            strategy="known_ids",
            id_field="id",
            flatten="gitlab.mr",
        ),
        PollingEvent(
            id="new_release",
            label="New Release",
            list_path="{base_url}/api/v4/projects/{project_id}/releases",
            strategy="known_ids",
            id_field="tag_name",
            flatten="gitlab.release",
        ),
        PollingEvent(
            id="new_commit",
            label="New Commit",
            list_path="{base_url}/api/v4/projects/{project_id}/repository/commits",
            list_params={"per_page": "20"},
            strategy="known_ids",
            id_field="id",
            flatten="gitlab.commit",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "state", "type": "string"},
        {"label": "web_url", "type": "string"},
        {"label": "event_type", "type": "string"},
    ],
    paginate_fn=_walk_gitlab,
)
