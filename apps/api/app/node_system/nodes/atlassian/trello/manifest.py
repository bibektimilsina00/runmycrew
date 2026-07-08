"""Trello action node — manifest form.

Trello v1 REST API at `https://api.trello.com/1`. Auth rides in the
URL — `?key={app_key}&token={api_key}`. We use `auth="none"` and
attach both via a query_builder wrapper on every op.

Actually: cleaner to prepend `key` + `token` universally through
the auth scheme. The scaffold's `query_token` scheme puts one token
in a named param. Trello needs TWO — we exploit extra_headers
substitution + a per-op query_builder that reads them from the
credential via _PropCredView.
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.atlassian.trello import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)


def _auth_qs(v):
    """Prepend Trello's `key` + `token` params to every op's query."""
    return {
        "key": getattr(v, "app_key", None) or "",
        "token": getattr(v, "api_key", None) or "",
    }


def _q(v, **extra):
    return {**_auth_qs(v), **{k: val for k, val in extra.items() if val is not None}}


MANIFEST = ProviderManifest(
    type="action.trello",
    name=NAME,
    category="integration",
    description="Trello — boards, lists, cards.",
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://api.trello.com/1",
    credential_type="trello_api_key",
    token_field=["api_key"],
    # Custom-auth pattern — the two credential fields ride via each
    # op's query_builder rather than a shared auth scheme. `auth=none`
    # to skip the scaffold's own Authorization header build.
    auth="none",
    fields=[
        FieldSpec(name="board_id", label="Board ID", type="string"),
        FieldSpec(name="list_id", label="List ID", type="string"),
        FieldSpec(name="card_id", label="Card ID", type="string"),
        FieldSpec(name="name", label="Name", type="string"),
        FieldSpec(name="desc", label="Description", type="string", mode="advanced"),
        FieldSpec(name="pos", label="Position", type="string", default="bottom", mode="advanced"),
        FieldSpec(name="due", label="Due date (ISO)", type="string", mode="advanced"),
        FieldSpec(name="closed", label="Closed", type="boolean", mode="advanced"),
        FieldSpec(name="comment_text", label="Comment", type="string"),
    ],
    operations=[
        OpSpec(
            id="get_me",
            label="Get Me",
            method="GET",
            path="/members/me",
            query_builder=_auth_qs,
        ),
        OpSpec(
            id="list_boards",
            label="List My Boards",
            method="GET",
            path="/members/me/boards",
            query_builder=_auth_qs,
        ),
        OpSpec(
            id="get_board",
            label="Get Board",
            method="GET",
            path="/boards/{board_id}",
            visible_fields=["board_id"],
            query_builder=_auth_qs,
        ),
        OpSpec(
            id="list_lists",
            label="List Lists on Board",
            method="GET",
            path="/boards/{board_id}/lists",
            visible_fields=["board_id"],
            query_builder=_auth_qs,
        ),
        OpSpec(
            id="create_list",
            label="Create List",
            method="POST",
            path="/lists",
            visible_fields=["board_id", "name", "pos"],
            query_builder=lambda v: _q(
                v,
                idBoard=getattr(v, "board_id", None) or "",
                name=getattr(v, "name", None) or "",
                pos=getattr(v, "pos", None) or "bottom",
            ),
        ),
        OpSpec(
            id="list_cards",
            label="List Cards on List",
            method="GET",
            path="/lists/{list_id}/cards",
            visible_fields=["list_id"],
            query_builder=_auth_qs,
        ),
        OpSpec(
            id="get_card",
            label="Get Card",
            method="GET",
            path="/cards/{card_id}",
            visible_fields=["card_id"],
            query_builder=_auth_qs,
        ),
        OpSpec(
            id="create_card",
            label="Create Card",
            method="POST",
            path="/cards",
            visible_fields=["list_id", "name", "desc", "due", "pos"],
            query_builder=lambda v: _q(
                v,
                idList=getattr(v, "list_id", None) or "",
                name=getattr(v, "name", None) or "",
                desc=getattr(v, "desc", None),
                due=getattr(v, "due", None),
                pos=getattr(v, "pos", None) or "bottom",
            ),
        ),
        OpSpec(
            id="update_card",
            label="Update Card",
            method="PUT",
            path="/cards/{card_id}",
            visible_fields=["card_id", "name", "desc", "due", "closed", "list_id"],
            query_builder=lambda v: _q(
                v,
                name=getattr(v, "name", None),
                desc=getattr(v, "desc", None),
                due=getattr(v, "due", None),
                closed=(str(v.closed).lower() if getattr(v, "closed", None) is not None else None),
                idList=getattr(v, "list_id", None),
            ),
        ),
        OpSpec(
            id="delete_card",
            label="Delete Card",
            method="DELETE",
            path="/cards/{card_id}",
            visible_fields=["card_id"],
            query_builder=_auth_qs,
            success_payload_template={"deleted": True, "card_id": "{card_id}"},
        ),
        OpSpec(
            id="add_comment",
            label="Add Card Comment",
            method="POST",
            path="/cards/{card_id}/actions/comments",
            visible_fields=["card_id", "comment_text"],
            query_builder=lambda v: _q(v, text=getattr(v, "comment_text", None) or ""),
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "url", "type": "string"},
        {"label": "items", "type": "array"},
    ],
    allow_error=True,
)
