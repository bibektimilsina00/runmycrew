"""Google Chat action node — one node, 12 operations.

Space + membership reads
  - ``list_spaces``        — paged list, filter by space type
  - ``get_space``          — fetch a single space by resource name
  - ``list_members``       — paged member list
  - ``find_direct_message`` — locate the DM space with another user

Message lifecycle
  - ``send_message``    — text + optional Card v2 JSON, optional thread key
  - ``update_message``  — replace text on an existing message
  - ``delete_message``  — by resource name
  - ``list_messages``   — paged, ordered, optional createTime filter
  - ``get_message``     — by resource name

Reactions
  - ``add_reaction``    — unicode emoji on a message
  - ``list_reactions``  — paged
  - ``delete_reaction`` — by reaction resource name

OAuth scopes used (all added to GoogleOAuthProvider):
``chat.messages``, ``chat.messages.reactions``,
``chat.spaces.readonly``, ``chat.memberships.readonly``.

Notes from build
  - Chat resource names are first-class identifiers. The space picker
    emits ``{id, name}`` (where ``id`` is the bare space id like ``AAAA``)
    so the user can still see the display name in the editor; the
    runtime coerces the field down to the API path ``spaces/AAAA``.
  - For message-name / reaction-name fields the runtime accepts either
    the bare id or the full ``spaces/.../messages/...`` resource name
    and normalises both into the canonical resource path.
  - ``cards`` accepts a dict or a JSON string; either is forwarded
    verbatim under ``cardsV2`` so workflow authors keep full control
    over Chat Card v2 layout.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import BaseModel, field_validator

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.errors import make_structured_error
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

CHAT_API = "https://chat.googleapis.com/v1"


def format_chat_error(status_code: int, body: str) -> str:
    """Turn a Chat API HTTP error into a structured error payload.

    Known setup-gap statuses (product off, app not configured, scope
    missing, quota, etc) return a sentinel-prefixed JSON payload via
    :func:`make_structured_error` so the inspector renders a polished
    card: title + plain-English summary + bulleted actions + raw body
    in a collapsible section.

    Unhandled statuses fall through to a plain string — the default
    error renderer keeps working with no information loss.

    Setup gaps users most often hit:
      1. **Google Chat is turned off** on the connected account
         (Workspace admin → Apps → Chat, or for personal accounts
         Gmail → Settings → Chat and Meet).
      2. **Chat API library not enabled** in the GCP project
         (Console → APIs & Services → Library → enable
         ``chat.googleapis.com``).
      3. **Chat app not configured** — separate from #2; Console →
         APIs & Services → Google Chat API → Configuration tab.
    """
    snippet = (body or "").strip()[:600]
    lower = snippet.lower()

    if status_code == 400 and "google chat is turned off" in lower:
        return make_structured_error(
            "Google Chat is turned off on the connected account",
            summary=(
                "The Chat API works only when Google Chat is enabled as "
                "a product on the user's Google account. Per-account "
                "setting, separate from the API in GCP."
            ),
            actions=[
                "Workspace: Admin Console → Apps → Google Workspace → Google Chat → ON.",
                "Personal account: Gmail → ⚙ Settings → Chat and Meet → Chat = Google Chat.",
                "Wait ~1 minute for propagation, then retry.",
            ],
            raw=snippet,
        )

    if status_code == 403 and "permission_denied" in lower:
        return make_structured_error(
            "Google Chat API rejected the request",
            summary=(
                "Either the Chat API isn't enabled for this GCP project, "
                "or the OAuth token doesn't carry the chat.* scopes "
                "needed for this operation."
            ),
            actions=[
                "GCP Console → APIs & Services → Library → enable `chat.googleapis.com`.",
                "Fuse → Credentials → disconnect this Google account and reconnect to grant the new chat.* scopes.",
            ],
            raw=snippet,
        )

    if status_code == 404 and "chat app not found" in lower:
        return make_structured_error(
            "Chat app not configured in this GCP project",
            summary=(
                "The Chat API needs a Chat app configuration row in "
                "your GCP project — separate from enabling the API "
                "library. Even user-OAuth calls are rejected without it."
            ),
            actions=[
                "GCP Console → APIs & Services → Google Chat API → Configuration tab.",
                "Fill in App name, avatar URL, and description.",
                "Save the configuration, then retry the workflow.",
            ],
            raw=snippet,
        )

    if status_code == 404:
        return make_structured_error(
            "Resource not found",
            summary=(
                "The connected Google account may not be a member of "
                "this space, or the resource name is stale."
            ),
            actions=[
                "Re-open the space picker and re-select the space.",
                "If you typed the resource name, verify it matches `spaces/...` exactly.",
                "Make sure the connected account is a member of the space in Chat.",
            ],
            raw=snippet,
        )

    if status_code == 401:
        return make_structured_error(
            "Google credential is no longer valid",
            summary=(
                "The OAuth token has expired or the chat.* scopes were "
                "revoked from the Google account settings."
            ),
            actions=[
                "Fuse → Credentials → disconnect and reconnect the Google account.",
            ],
            raw=snippet,
        )

    if status_code == 429:
        return make_structured_error(
            "Google Chat API quota exceeded",
            summary=(
                "The project has run out of Chat API quota for the "
                "current window. Calls will resume once the quota "
                "refills (usually within a minute)."
            ),
            actions=[
                "Wait and retry — the quota refills automatically.",
                "If this keeps happening, raise the quota in GCP Console → IAM & Admin → Quotas.",
            ],
            raw=snippet,
        )

    # Unhandled status — fall through to plain string. Default frontend
    # error renderer still shows the user the raw body.
    return f"Google Chat API error {status_code}: {snippet or '(no body)'}"


_SPACE_TYPE_FILTER_OPTIONS: list[dict[str, str]] = [
    {"label": "All", "value": ""},
    {"label": "Spaces (rooms)", "value": 'spaceType = "SPACE"'},
    {"label": "Direct messages", "value": 'spaceType = "DIRECT_MESSAGE"'},
    {"label": "Group chats", "value": 'spaceType = "GROUP_CHAT"'},
]


class GoogleChatProperties(BaseModel):
    credential: str | None = None
    operation: str = "send_message"

    # Space / message / reaction identifiers — emitted by pickers or
    # typed in directly.
    space: str | None = None
    message_name: str | None = None
    reaction_name: str | None = None

    # send_message / update_message
    text: str | None = None
    cards: Any = None  # accept dict OR JSON string
    thread_key: str | None = None

    # find_direct_message
    user_resource: str | None = None

    # reactions
    emoji: str | None = None

    # list_* paging + filtering
    filter: str | None = None
    page_size: int | None = None
    page_token: str | None = None
    order_by: str | None = None

    # list_spaces type filter (canned)
    space_type_filter: str | None = None

    @field_validator("space", mode="before")
    @classmethod
    def _coerce_space(cls, value: Any) -> str | None:
        """Space picker emits ``{id, name, type}``; the rest of the
        runtime needs the canonical resource path ``spaces/{id}``.
        Accept also a bare id or the full path so manual entry works."""
        if value in (None, ""):
            return None
        if isinstance(value, dict):
            v = value.get("id") or value.get("name") or ""
            if not v:
                return None
            return _to_space_name(str(v))
        return _to_space_name(str(value))

    @field_validator("message_name", "reaction_name", "user_resource", mode="before")
    @classmethod
    def _strip_str(cls, value: Any) -> str | None:
        if value in (None, ""):
            return None
        return str(value).strip() or None


def _to_space_name(raw: str) -> str:
    """Normalise space input — bare id ``AAAA`` → ``spaces/AAAA``;
    full path passes through unchanged."""
    raw = raw.strip()
    if not raw:
        return raw
    return raw if raw.startswith("spaces/") else f"spaces/{raw}"


def _normalise_message_name(space: str | None, raw: str) -> str:
    """Accept either a full ``spaces/X/messages/Y`` path or a bare
    message id (in which case the configured space is required)."""
    raw = raw.strip()
    if raw.startswith("spaces/") and "/messages/" in raw:
        return raw
    if not space:
        raise ValueError(
            "Message ID alone is ambiguous — also set Space, or paste the "
            "full `spaces/.../messages/...` resource name."
        )
    return f"{space.rstrip('/')}/messages/{raw}"


def _normalise_reaction_name(raw: str) -> str:
    """Reactions live under messages; only the full path is unambiguous."""
    raw = raw.strip()
    if "/reactions/" not in raw:
        raise ValueError(
            "Reaction resource name must include the full "
            "`spaces/.../messages/.../reactions/...` path."
        )
    return raw


def _cond(op: str) -> dict[str, Any]:
    return {"field": "operation", "value": op}


def _cond_any(*ops: str) -> dict[str, Any]:
    return {"field": "operation", "value": list(ops)}


class GoogleChatNode(BaseNode[GoogleChatProperties]):
    @classmethod
    def get_properties_model(cls):
        return GoogleChatProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.gchat",
            name="Google Chat",
            category="integration",
            description=(
                "Post messages and cards into Google Chat spaces / DMs, "
                "read history, react to messages, and look up space "
                "members — driven by the connected Google account."
            ),
            icon="si:SiGooglechat",
            color="#1a73e8",
            properties=[
                {
                    "name": "credential",
                    "label": "Google Account",
                    "type": "credential",
                    "credentialType": "google_oauth",
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "send_message",
                    "options": [
                        {"label": "Send message", "value": "send_message"},
                        {"label": "Update message", "value": "update_message"},
                        {"label": "Delete message", "value": "delete_message"},
                        {"label": "List messages", "value": "list_messages"},
                        {"label": "Get message", "value": "get_message"},
                        {"label": "List spaces", "value": "list_spaces"},
                        {"label": "Get space", "value": "get_space"},
                        {"label": "List members", "value": "list_members"},
                        {"label": "Find direct message (by user)", "value": "find_direct_message"},
                        {"label": "Add reaction", "value": "add_reaction"},
                        {"label": "List reactions", "value": "list_reactions"},
                        {"label": "Delete reaction", "value": "delete_reaction"},
                    ],
                },
                {
                    "name": "space",
                    "label": "Space",
                    "type": "gchat-space",
                    "required": True,
                    "condition": _cond_any(
                        "send_message",
                        "list_messages",
                        "get_space",
                        "list_members",
                    ),
                },
                # send_message / update_message body
                {
                    "name": "text",
                    "label": "Message text",
                    "type": "string",
                    "typeOptions": {"multiline": True, "rows": 4},
                    "placeholder": "Hello from Fuse — {{ $trigger.summary }}",
                    "condition": _cond_any("send_message", "update_message"),
                },
                {
                    "name": "cards",
                    "label": "Cards (Card v2 JSON)",
                    "type": "json",
                    "placeholder": (
                        '[ { "cardId": "c1", "card": { "header": { "title": "Hi" } } } ]'
                    ),
                    "description": (
                        "Optional. Forwarded verbatim under `cardsV2`. Pass either a JSON "
                        "array of cards or a single card object — the node wraps a single "
                        "card with a generated cardId."
                    ),
                    "condition": _cond("send_message"),
                    "mode": "advanced",
                },
                {
                    "name": "thread_key",
                    "label": "Thread key",
                    "type": "string",
                    "placeholder": "Optional — reply key used to group messages",
                    "description": (
                        "If set, the new message joins (or starts) the thread identified "
                        "by this key. Useful when you want incident-style updates to land "
                        "under one thread per ticket id."
                    ),
                    "condition": _cond("send_message"),
                    "mode": "advanced",
                },
                # message-name targeting
                {
                    "name": "message_name",
                    "label": "Message",
                    "type": "string",
                    "required": True,
                    "placeholder": "spaces/AAAA/messages/BBBB",
                    "description": (
                        "Full resource name. Hit Send message first and bind "
                        "`{{ $node('Google Chat').name }}` to update / delete it later."
                    ),
                    "condition": _cond_any(
                        "update_message",
                        "delete_message",
                        "get_message",
                        "add_reaction",
                        "list_reactions",
                    ),
                },
                # find_direct_message
                {
                    "name": "user_resource",
                    "label": "User resource",
                    "type": "string",
                    "required": True,
                    "placeholder": "users/123456789",
                    "description": (
                        "The other party's user id. Use `users/{id}` for a Workspace "
                        "user, or `users/{email}` if their address is enumerable."
                    ),
                    "condition": _cond("find_direct_message"),
                },
                # reactions
                {
                    "name": "emoji",
                    "label": "Emoji",
                    "type": "string",
                    "required": True,
                    "placeholder": "👍",
                    "description": "Single unicode emoji (Chat accepts unicode only).",
                    "condition": _cond("add_reaction"),
                },
                {
                    "name": "reaction_name",
                    "label": "Reaction",
                    "type": "string",
                    "required": True,
                    "placeholder": "spaces/AAAA/messages/BBBB/reactions/CCCC",
                    "condition": _cond("delete_reaction"),
                },
                # list filters
                {
                    "name": "space_type_filter",
                    "label": "Type",
                    "type": "options",
                    "default": "",
                    "options": _SPACE_TYPE_FILTER_OPTIONS,
                    "condition": _cond("list_spaces"),
                },
                {
                    "name": "filter",
                    "label": "Filter (CEL)",
                    "type": "string",
                    "placeholder": 'createTime > "2025-01-01T00:00:00Z"',
                    "description": (
                        "Optional Chat API CEL filter — overrides the canned Type filter "
                        "above for list_spaces; on list_messages it limits to messages "
                        "matching the createTime / lastUpdateTime predicate."
                    ),
                    "condition": _cond_any("list_spaces", "list_messages", "list_members"),
                    "mode": "advanced",
                },
                {
                    "name": "order_by",
                    "label": "Order by",
                    "type": "string",
                    "placeholder": "createTime desc",
                    "condition": _cond("list_messages"),
                    "mode": "advanced",
                },
                {
                    "name": "page_size",
                    "label": "Page size",
                    "type": "number",
                    "default": 50,
                    "condition": _cond_any(
                        "list_spaces", "list_messages", "list_members", "list_reactions"
                    ),
                    "mode": "advanced",
                },
                {
                    "name": "page_token",
                    "label": "Page token",
                    "type": "string",
                    "placeholder": "{{ $node('Google Chat').nextPageToken }}",
                    "condition": _cond_any(
                        "list_spaces", "list_messages", "list_members", "list_reactions"
                    ),
                    "mode": "advanced",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "name", "type": "string"},
                {"label": "text", "type": "string"},
                {"label": "sender", "type": "object"},
                {"label": "createTime", "type": "string"},
                {"label": "thread", "type": "object"},
            ],
            allow_error=True,
            credential_type="google_oauth",
        )

    def _get_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="Google OAuth credential required.")

        op = self.props.operation
        handler = _HANDLERS.get(op)
        if handler is None:
            return NodeResult(success=False, error=f"Unknown operation: {op}")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                return await handler(self, client, headers)
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=format_chat_error(exc.response.status_code, exc.response.text),
            )
        except ValueError as exc:
            # Raised by _normalise_message_name / _normalise_reaction_name
            # when the caller hasn't provided enough context — user-facing
            # input errors, surface them cleanly.
            return NodeResult(success=False, error=str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GoogleChatNode {op} failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))


# ── shared helpers ──────────────────────────────────────────────────────


def _require_space(node: GoogleChatNode) -> str | NodeResult:
    space = (node.props.space or "").strip()
    if not space:
        return NodeResult(success=False, error="Space is required.")
    return space


def _require_message(node: GoogleChatNode) -> str | NodeResult:
    raw = (node.props.message_name or "").strip()
    if not raw:
        return NodeResult(success=False, error="Message is required.")
    try:
        return _normalise_message_name(node.props.space, raw)
    except ValueError as exc:
        return NodeResult(success=False, error=str(exc))


def _build_paging_params(node: GoogleChatNode) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if node.props.page_size:
        params["pageSize"] = max(1, min(int(node.props.page_size), 1000))
    if node.props.page_token:
        params["pageToken"] = node.props.page_token
    return params


def _coerce_cards(raw: Any) -> list[dict[str, Any]] | None:
    """Accept dict, list, or JSON string for the cards property.

    Single-card dicts are wrapped into a one-element ``cardsV2`` list
    with a generated ``cardId`` so the caller never has to write the
    enclosing array shape themselves."""
    if raw in (None, "", []):
        return None
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"`cards` must be valid JSON: {exc.msg}") from exc
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        # Heuristic: a CardWithId entry has top-level `card` (the body)
        # and `cardId`. A bare Card object has `header`/`sections`. Wrap
        # the bare form.
        if "card" in raw and isinstance(raw.get("card"), dict):
            return [raw]
        return [{"cardId": "fuse_card", "card": raw}]
    raise ValueError("`cards` must be an object, array, or JSON string.")


# ── handlers ────────────────────────────────────────────────────────────


async def _send_message(
    node: GoogleChatNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    space = _require_space(node)
    if isinstance(space, NodeResult):
        return space
    text = node.props.text or ""
    cards = _coerce_cards(node.props.cards)
    if not text.strip() and not cards:
        return NodeResult(success=False, error="Provide `text`, `cards`, or both.")

    body: dict[str, Any] = {}
    if text:
        body["text"] = text
    if cards:
        body["cardsV2"] = cards

    params: dict[str, Any] = {}
    thread_key = (node.props.thread_key or "").strip()
    if thread_key:
        body["thread"] = {"threadKey": thread_key}
        # Tells the API to attach to an existing thread when the key
        # matches, otherwise start a new thread (instead of failing).
        params["messageReplyOption"] = "REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"

    r = await client.post(
        f"{CHAT_API}/{space}/messages",
        headers=headers,
        json=body,
        params=params,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _update_message(
    node: GoogleChatNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    name = _require_message(node)
    if isinstance(name, NodeResult):
        return name
    text = node.props.text or ""
    if not text.strip():
        return NodeResult(success=False, error="`text` is required for update_message.")
    # The Chat API requires an explicit `updateMask` to know which
    # fields the body wants overwritten. We expose `text` only here;
    # users wanting to change cards should re-send or use the dedicated
    # cards path in a future op.
    r = await client.patch(
        f"{CHAT_API}/{name}",
        headers=headers,
        params={"updateMask": "text"},
        json={"text": text},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _delete_message(
    node: GoogleChatNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    name = _require_message(node)
    if isinstance(name, NodeResult):
        return name
    r = await client.delete(f"{CHAT_API}/{name}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data={"name": name, "deleted": True})


async def _list_messages(
    node: GoogleChatNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    space = _require_space(node)
    if isinstance(space, NodeResult):
        return space
    params = _build_paging_params(node)
    if node.props.filter:
        params["filter"] = node.props.filter
    if node.props.order_by:
        params["orderBy"] = node.props.order_by
    r = await client.get(f"{CHAT_API}/{space}/messages", headers=headers, params=params)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _get_message(
    node: GoogleChatNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    name = _require_message(node)
    if isinstance(name, NodeResult):
        return name
    r = await client.get(f"{CHAT_API}/{name}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _list_spaces(
    node: GoogleChatNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    params = _build_paging_params(node)
    # The free-form `filter` field takes precedence over the canned
    # space-type radio so power users can express anything CEL supports.
    flt = (node.props.filter or "").strip()
    if not flt:
        flt = (node.props.space_type_filter or "").strip()
    if flt:
        params["filter"] = flt
    r = await client.get(f"{CHAT_API}/spaces", headers=headers, params=params)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _get_space(
    node: GoogleChatNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    space = _require_space(node)
    if isinstance(space, NodeResult):
        return space
    r = await client.get(f"{CHAT_API}/{space}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _list_members(
    node: GoogleChatNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    space = _require_space(node)
    if isinstance(space, NodeResult):
        return space
    params = _build_paging_params(node)
    if node.props.filter:
        params["filter"] = node.props.filter
    r = await client.get(f"{CHAT_API}/{space}/members", headers=headers, params=params)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _find_direct_message(
    node: GoogleChatNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    user = (node.props.user_resource or "").strip()
    if not user:
        return NodeResult(success=False, error="`user_resource` is required.")
    if not user.startswith("users/"):
        user = f"users/{user}"
    r = await client.get(
        f"{CHAT_API}/spaces/findDirectMessage",
        headers=headers,
        params={"name": user},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _add_reaction(
    node: GoogleChatNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    name = _require_message(node)
    if isinstance(name, NodeResult):
        return name
    emoji = (node.props.emoji or "").strip()
    if not emoji:
        return NodeResult(success=False, error="`emoji` is required.")
    r = await client.post(
        f"{CHAT_API}/{name}/reactions",
        headers=headers,
        json={"emoji": {"unicode": emoji}},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _list_reactions(
    node: GoogleChatNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    name = _require_message(node)
    if isinstance(name, NodeResult):
        return name
    params = _build_paging_params(node)
    r = await client.get(f"{CHAT_API}/{name}/reactions", headers=headers, params=params)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _delete_reaction(
    node: GoogleChatNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    raw = (node.props.reaction_name or "").strip()
    if not raw:
        return NodeResult(success=False, error="`reaction_name` is required.")
    try:
        name = _normalise_reaction_name(raw)
    except ValueError as exc:
        return NodeResult(success=False, error=str(exc))
    r = await client.delete(f"{CHAT_API}/{name}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data={"name": name, "deleted": True})


_HANDLERS: dict[str, Any] = {
    "send_message": _send_message,
    "update_message": _update_message,
    "delete_message": _delete_message,
    "list_messages": _list_messages,
    "get_message": _get_message,
    "list_spaces": _list_spaces,
    "get_space": _get_space,
    "list_members": _list_members,
    "find_direct_message": _find_direct_message,
    "add_reaction": _add_reaction,
    "list_reactions": _list_reactions,
    "delete_reaction": _delete_reaction,
}
