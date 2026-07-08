"""Trello polling trigger — manifest form.

Watches a board's actions (card created, list updated, etc.).
Trello auth rides in the query string as `?key={app_key}&token={api_key}` —
same as the action node. paginate_fn handles the auth injection since
scaffold's built-in auth schemes only carry one credential field.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.node_system.nodes.atlassian.trello import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)
from apps.api.app.node_system.scaffolds.field_resolvers import resolve_template


def _flatten_action(item):
    data = item.get("data") or {}
    return {
        "id": item.get("id"),
        "type": item.get("type"),
        "date": item.get("date"),
        "member_creator": (item.get("memberCreator") or {}).get("username"),
        "card_id": (data.get("card") or {}).get("id"),
        "card_name": (data.get("card") or {}).get("name"),
        "list_id": (data.get("list") or {}).get("id"),
        "list_name": (data.get("list") or {}).get("name"),
        "board_id": (data.get("board") or {}).get("id"),
    }


register_flatten("trello.action", _flatten_action)


async def _walk_trello(
    client: httpx.AsyncClient,
    *,
    manifest,
    event,
    token: str | None,
    props: Any,
) -> list[dict[str, Any]]:
    """Trello wants key + token as query params. Pull both from
    credential, resolve list_path against the merged view."""
    cred = getattr(props, "_cred", None) or {}
    url = resolve_template(manifest.base_url + event.list_path, props)
    params = {
        "key": cred.get("app_key") or "",
        "token": token or cred.get("api_key") or "",
        **{
            k: (resolve_template(v, props) if isinstance(v, str) else v)
            for k, v in (event.list_params or {}).items()
        },
    }
    resp = await client.get(url, params=params, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    return body if isinstance(body, list) else []


MANIFEST = PollingTriggerManifest(
    type="trigger.trello",
    name=NAME,
    description="Poll a Trello board for new actions (cards, comments, moves).",
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://api.trello.com/1",
    credential_type="trello_api_key",
    token_field=["api_key"],
    # auth=none — key+token ride via paginate_fn as query params.
    auth="none",
    provider="trello",
    default_poll_interval_seconds=60,
    common_fields=[
        FieldSpec(
            name="board_id",
            label="Board ID",
            type="string",
            required=True,
        ),
        FieldSpec(
            name="limit",
            label="Limit",
            type="number",
            default=25,
            mode="advanced",
        ),
    ],
    events=[
        PollingEvent(
            id="new_card",
            label="Card Created",
            list_path="/boards/{board_id}/actions",
            list_params={"filter": "createCard", "limit": "{limit}"},
            strategy="known_ids",
            id_field="id",
            flatten="trello.action",
        ),
        PollingEvent(
            id="card_updated",
            label="Card Updated",
            list_path="/boards/{board_id}/actions",
            list_params={"filter": "updateCard", "limit": "{limit}"},
            strategy="known_ids",
            id_field="id",
            flatten="trello.action",
        ),
        PollingEvent(
            id="new_comment",
            label="Comment on Card",
            list_path="/boards/{board_id}/actions",
            list_params={"filter": "commentCard", "limit": "{limit}"},
            strategy="known_ids",
            id_field="id",
            flatten="trello.action",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "type", "type": "string"},
        {"label": "date", "type": "string"},
        {"label": "card_id", "type": "string"},
        {"label": "card_name", "type": "string"},
        {"label": "event_type", "type": "string"},
    ],
    paginate_fn=_walk_trello,
)
