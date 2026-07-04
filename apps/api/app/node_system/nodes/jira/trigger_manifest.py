"""Jira polling trigger — manifest form.

Jira Cloud REST v3 at `{base_url}/rest/api/3`.
Basic auth using `{email}:{api_key}`. The scaffold's basic-auth
scheme with `auth_basic_username="{email}"` handles the auth; the
manifest reads the subdomain from the credential dict via templates
in list_path.

Events use `known_ids` on issue ids; JQL-based `since_timestamp`
would need an ORDER BY updated ASC + since filter, harder to keep
consistent across polls than a set-diff.
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


def _flatten_issue(item):
    fields = item.get("fields") or {}
    return {
        "key": item.get("key"),
        "id": item.get("id"),
        "summary": fields.get("summary"),
        "status": (fields.get("status") or {}).get("name"),
        "priority": (fields.get("priority") or {}).get("name"),
        "assignee": (fields.get("assignee") or {}).get("displayName"),
        "reporter": (fields.get("reporter") or {}).get("displayName"),
        "created": fields.get("created"),
        "updated": fields.get("updated"),
        "url": item.get("self"),
    }


register_flatten("jira.issue", _flatten_issue)


async def _walk_jira(
    client: httpx.AsyncClient,
    *,
    manifest,
    event,
    token: str | None,
    props: Any,
) -> list[dict[str, Any]]:
    """Jira Cloud search endpoint returns `{issues: [...], total}`.
    Fetch one page (up to 100), the scaffold's diff strategy handles
    the rest."""
    cred = getattr(props, "_cred", None) or {}
    base_url = (cred.get("base_url") or "").rstrip("/")
    url = resolve_template(
        event.list_path.replace("{base_url}", base_url),
        props,
    )
    params = dict(event.list_params or {})
    auth_headers, _ = build_auth(
        token=token,
        scheme="basic",
        header_name="Authorization",
        value_template="",
        query_param="",
        basic_username=cred.get("email") or "",
    )
    headers = {**auth_headers, "Accept": "application/json"}
    resp = await client.get(url, headers=headers, params=params or None, timeout=30)
    resp.raise_for_status()
    body = resp.json() or {}
    return body.get("issues") or []


MANIFEST = PollingTriggerManifest(
    type="trigger.jira",
    name="Jira",
    description="Poll Jira for new / recently-updated issues matching a JQL query.",
    icon_slug="jira",
    color="#1c1c1c",
    base_url="",
    credential_type="jira_api_key",
    token_field=["api_key"],
    auth="basic",
    provider="jira",
    default_poll_interval_seconds=90,
    common_fields=[
        FieldSpec(
            name="jql",
            label="JQL",
            type="string",
            required=True,
            placeholder='project = "ABC" AND status = "To Do"',
        ),
        FieldSpec(
            name="max_results",
            label="Max Results",
            type="number",
            default=50,
            mode="advanced",
        ),
    ],
    events=[
        PollingEvent(
            id="new_issue",
            label="New Issue Matching JQL",
            list_path="{base_url}/rest/api/3/search",
            list_params={"jql": "{jql}", "maxResults": "{max_results}"},
            strategy="known_ids",
            id_field="id",
            flatten="jira.issue",
        ),
        PollingEvent(
            id="issue_updated",
            label="Issue Updated",
            list_path="{base_url}/rest/api/3/search",
            list_params={
                "jql": "{jql} ORDER BY updated DESC",
                "maxResults": "{max_results}",
                "expand": "changelog",
            },
            strategy="since_timestamp",
            timestamp_field="updated",
            flatten="jira.issue",
        ),
    ],
    outputs_schema=[
        {"label": "key", "type": "string"},
        {"label": "id", "type": "string"},
        {"label": "summary", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "assignee", "type": "string"},
        {"label": "updated", "type": "string"},
    ],
    paginate_fn=_walk_jira,
)
