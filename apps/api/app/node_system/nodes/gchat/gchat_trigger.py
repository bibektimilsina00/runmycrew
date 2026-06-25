"""Google Chat trigger node — polling-driven message detection.

One event today:

  - ``new_message_in_space`` — fires once per new message posted to
    the chosen space (or DM). Cursor shape:
    ``{event_type: "new_message_in_space", last_create_time: ISO-8601}``.

    First poll captures the most recent message's ``createTime`` and
    emits nothing. Later polls query
    ``messages.list?filter=createTime > "<cursor>"`` and emit one
    execution per match (capped by ``max_per_poll``).

The Chat API only supports webhook events from a *bot user* — i.e. an
app installed into a workspace. Polling lets us deliver this trigger
under the same OAuth provider every other Google surface uses, with no
extra app-install dance for the customer.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel, field_validator

from apps.api.app.core.logger import get_logger
from apps.api.app.features.triggers.repository import IntegrationTriggerStateRepository
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

CHAT_API = "https://chat.googleapis.com/v1"
PROVIDER = "google_chat"
DEFAULT_POLL_INTERVAL_SECONDS = 60

EVENT_NEW_MESSAGE = "new_message_in_space"
EVENT_TYPES = (EVENT_NEW_MESSAGE,)


class GoogleChatTriggerProperties(BaseModel):
    credential: str | None = None
    event_type: str = EVENT_NEW_MESSAGE
    space: str = ""
    # Optional CEL fragment AND-ed with the createTime cursor filter.
    # Lets the user limit to e.g. messages mentioning a specific user.
    extra_filter: str | None = None
    max_per_poll: int = 25
    poll_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS

    @field_validator("space", mode="before")
    @classmethod
    def _coerce_space(cls, value: Any) -> str:
        from apps.api.app.node_system.nodes.gchat.gchat_node import _to_space_name

        if value in (None, ""):
            return ""
        if isinstance(value, dict):
            v = value.get("id") or value.get("name") or ""
            return _to_space_name(str(v)) if v else ""
        return _to_space_name(str(value))

    @field_validator("event_type", mode="before")
    @classmethod
    def _coerce_event_type(cls, value: Any) -> str:
        v = str(value or "").strip().lower()
        return v if v in EVENT_TYPES else EVENT_NEW_MESSAGE


class GoogleChatTriggerNode(BaseNode[GoogleChatTriggerProperties]):
    @classmethod
    def get_properties_model(cls):
        return GoogleChatTriggerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.gchat_change",
            name="Google Chat",
            category="trigger",
            description=(
                "Fires when a new message is posted to the chosen Chat "
                "space or DM. First poll silently snapshots the cursor; "
                "later polls emit one execution per new message."
            ),
            icon="google-chat",
            color="#1c1c1c",
            properties=[
                {
                    "name": "credential",
                    "label": "Google Account",
                    "type": "credential",
                    "credentialType": "google_oauth",
                    "required": True,
                },
                {
                    "name": "event_type",
                    "label": "Event",
                    "type": "options",
                    "default": EVENT_NEW_MESSAGE,
                    "options": [
                        {"label": "New message in space", "value": EVENT_NEW_MESSAGE},
                    ],
                },
                {
                    "name": "space",
                    "label": "Space",
                    "type": "gchat-space",
                    "required": True,
                },
                {
                    "name": "extra_filter",
                    "label": "Extra filter (CEL)",
                    "type": "string",
                    "placeholder": 'sender.name = "users/123"',
                    "description": (
                        "Optional. Combined with the createTime cursor using `AND` "
                        "before being sent to messages.list — e.g. only messages "
                        "from a specific user."
                    ),
                    "mode": "advanced",
                },
                {
                    "name": "max_per_poll",
                    "label": "Max events per poll",
                    "type": "number",
                    "default": 25,
                    "mode": "advanced",
                },
                {
                    "name": "poll_interval_seconds",
                    "label": "Poll interval (seconds)",
                    "type": "number",
                    "default": DEFAULT_POLL_INTERVAL_SECONDS,
                    "mode": "advanced",
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "name", "type": "string"},
                {"label": "text", "type": "string"},
                {"label": "sender", "type": "object"},
                {"label": "space", "type": "string"},
                {"label": "createTime", "type": "string"},
                {"label": "thread", "type": "object"},
                {"label": "event_type", "type": "string"},
            ],
            allow_error=True,
            credential_type="google_oauth",
        )

    def _get_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        # Scheduler-dispatched payload — pass through.
        if (
            isinstance(input_data, dict)
            and input_data.get("name")
            and input_data.get("event_type") in EVENT_TYPES
        ):
            return NodeResult(success=True, output_data=input_data)

        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="Google OAuth credential required.")
        if not self.props.space:
            return NodeResult(success=False, error="Space is required.")

        workflow_id = getattr(context, "workflow_id", None)
        node_id = getattr(context, "node_id", None)
        workspace_id = getattr(context, "workspace_id", None)
        db = getattr(context, "db", None)
        wf_uuid = _safe_uuid(workflow_id)
        ws_uuid = _safe_uuid(workspace_id)
        if wf_uuid is None or ws_uuid is None or db is None or not node_id:
            return await self._stateless_preview(token)

        repo = IntegrationTriggerStateRepository(db)
        state = await repo.get(wf_uuid, node_id)
        cursor = state.cursor if state else None

        try:
            matches, new_cursor = await self.poll(token, cursor)
        except httpx.HTTPStatusError as exc:
            from apps.api.app.node_system.nodes.gchat.gchat_node import format_chat_error

            return NodeResult(
                success=False,
                error=format_chat_error(exc.response.status_code, exc.response.text),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("GoogleChatTriggerNode poll failed: %s", exc, exc_info=True)
            return NodeResult(success=False, error=str(exc))

        await repo.upsert(
            workflow_id=wf_uuid,
            workspace_id=ws_uuid,
            node_id=node_id,
            provider=PROVIDER,
            cursor=new_cursor,
            next_poll_at=_next_poll_at(self.props.poll_interval_seconds),
            last_error=None,
        )
        await db.commit()

        if not matches:
            return NodeResult(
                success=True,
                output_data={
                    "matched": 0,
                    "messages": [],
                    "event_type": self.props.event_type,
                    "last_create_time": new_cursor.get("last_create_time"),
                },
                handled_successors=True,
            )
        return NodeResult(success=True, output_data=matches[0])

    # ── public poll API ────────────────────────────────────────────────

    async def poll(
        self, token: str, cursor: dict[str, Any] | None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        headers = {"Authorization": f"Bearer {token}"}
        space = self.props.space
        max_per_poll = max(1, min(int(self.props.max_per_poll or 25), 500))

        # Cursor from a different event_type → start over with a fresh
        # snapshot for the current event setting.
        prior_event = (cursor or {}).get("event_type")
        if cursor and prior_event != self.props.event_type:
            cursor = None

        last_seen = (cursor or {}).get("last_create_time") or ""

        async with httpx.AsyncClient(timeout=30) as client:
            # First poll → snapshot only. We grab the single most recent
            # message and emit nothing.
            if not last_seen:
                snapshot = await _list_messages(
                    client,
                    headers,
                    space,
                    page_size=1,
                    order_by="createTime desc",
                )
                latest = (snapshot.get("messages") or [{}])[0] if snapshot else {}
                new_cursor_time = latest.get("createTime") or _now_iso()
                return [], {
                    "event_type": EVENT_NEW_MESSAGE,
                    "last_create_time": new_cursor_time,
                }

            filter_parts = [f'createTime > "{last_seen}"']
            extra = (self.props.extra_filter or "").strip()
            if extra:
                filter_parts.append(f"({extra})")
            data = await _list_messages(
                client,
                headers,
                space,
                page_size=max_per_poll,
                order_by="createTime asc",
                filter_=" AND ".join(filter_parts),
            )

        msgs = data.get("messages") or []
        matches = [_normalize(m, space, EVENT_NEW_MESSAGE) for m in msgs]
        # Advance the cursor to the newest seen message so the same
        # batch doesn't replay on the next tick.
        next_time = matches[-1]["createTime"] if matches else last_seen
        return matches, {
            "event_type": EVENT_NEW_MESSAGE,
            "last_create_time": next_time,
        }

    async def _stateless_preview(self, token: str) -> NodeResult:
        """Listen-mode preview path — no DB cursor available. Return
        the single most recent message as a sample event so users can
        see the shape they'll get."""
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            data = await _list_messages(
                client,
                headers,
                self.props.space,
                page_size=1,
                order_by="createTime desc",
            )
        msgs = data.get("messages") or []
        if not msgs:
            return NodeResult(
                success=True,
                output_data={
                    "matched": 0,
                    "messages": [],
                    "event_type": self.props.event_type,
                },
                handled_successors=True,
            )
        return NodeResult(
            success=True,
            output_data=_normalize(msgs[0], self.props.space, self.props.event_type),
        )


# ── helpers ─────────────────────────────────────────────────────────────


async def _list_messages(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    space: str,
    *,
    page_size: int,
    order_by: str,
    filter_: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "pageSize": page_size,
        "orderBy": order_by,
    }
    if filter_:
        params["filter"] = filter_
    r = await client.get(f"{CHAT_API}/{space}/messages", headers=headers, params=params)
    r.raise_for_status()
    return r.json()


def _normalize(msg: dict[str, Any], space: str, event_type: str) -> dict[str, Any]:
    return {
        "name": msg.get("name"),
        "text": msg.get("text") or "",
        "sender": msg.get("sender") or {},
        "createTime": msg.get("createTime") or "",
        "lastUpdateTime": msg.get("lastUpdateTime") or "",
        "thread": msg.get("thread") or {},
        "argumentText": msg.get("argumentText") or "",
        "space": space,
        "event_type": event_type,
        "payload": msg,
    }


def _safe_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None


def _next_poll_at(interval_seconds: int) -> datetime:
    seconds = max(30, min(int(interval_seconds or DEFAULT_POLL_INTERVAL_SECONDS), 60 * 60))
    return datetime.now(UTC) + timedelta(seconds=seconds)


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


# ── scheduler integration ──────────────────────────────────────────────


async def _poll_for_scheduler(
    token: str,
    cursor: dict[str, Any] | None,
    props: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from apps.api.app.node_system.nodes.gchat.gchat_node import _to_space_name

    raw_space = props.get("space") or ""
    if isinstance(raw_space, dict):
        raw_space = raw_space.get("id") or raw_space.get("name") or ""
    space = _to_space_name(str(raw_space)) if raw_space else ""

    node = GoogleChatTriggerNode.__new__(GoogleChatTriggerNode)
    node.props = GoogleChatTriggerProperties(
        credential=None,
        event_type=str(props.get("event_type") or EVENT_NEW_MESSAGE),
        space=space,
        extra_filter=props.get("extra_filter") or None,
        max_per_poll=int(props.get("max_per_poll") or 25),
        poll_interval_seconds=int(
            props.get("poll_interval_seconds") or DEFAULT_POLL_INTERVAL_SECONDS
        ),
    )
    return await node.poll(token, cursor)


def _register() -> None:
    try:
        from apps.api.app.execution_engine.scheduler.integration_polling import (
            register_poller,
        )
    except Exception:  # noqa: BLE001
        return
    register_poller(
        node_type="trigger.gchat_change",
        provider=PROVIDER,
        poller=_poll_for_scheduler,
    )


_register()
