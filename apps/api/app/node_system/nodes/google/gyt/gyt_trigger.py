"""YouTube trigger node — five polling events on the Data API + RSS.

Events
  - `new_comment`               — top-level comment on a video or your channel
  - `new_subscriber`            — new subscriber on your channel
  - `new_video`                 — new upload on a watched channel
                                  (own channel via Data API, other channels
                                  via the free RSS feed — zero quota)
  - `new_video_search_match`    — new public video matching a search query
                                  (brand monitoring etc.; expensive — default
                                  poll interval bumped to 5 min)
  - `new_reply_to_my_comment`   — reply posted under one of your top-level
                                  comments on any video

Cursors are tracked per event; switching the event treats the next poll
as the first poll so the cursor shapes don't cross-pollute.
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
from apps.api.app.node_system.nodes.google.gyt import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.nodes.google.gyt.gyt_node import (
    _flatten_comment,
    _flatten_subscription,
    _flatten_video,
)
from apps.api.app.node_system.nodes.google.gyt.gyt_rss import channel_feed_url, parse_feed

logger = get_logger(__name__)

YT_API = "https://www.googleapis.com/youtube/v3"
PROVIDER = "google_youtube"
DEFAULT_POLL_INTERVAL_SECONDS = 60

EVENT_NEW_COMMENT = "new_comment"
EVENT_NEW_SUBSCRIBER = "new_subscriber"
EVENT_NEW_VIDEO = "new_video"
EVENT_SEARCH_MATCH = "new_video_search_match"
EVENT_REPLY_TO_MY_COMMENT = "new_reply_to_my_comment"
EVENT_TYPES = (
    EVENT_NEW_COMMENT,
    EVENT_NEW_SUBSCRIBER,
    EVENT_NEW_VIDEO,
    EVENT_SEARCH_MATCH,
    EVENT_REPLY_TO_MY_COMMENT,
)


_VIDEO_SOURCE_OPTIONS: list[dict[str, str]] = [
    {"label": "My channel (API)", "value": "own"},
    {"label": "Another channel (RSS feed — no quota)", "value": "rss"},
]


class GoogleYouTubeTriggerProperties(BaseModel):
    credential: str | None = None
    event_type: str = EVENT_NEW_COMMENT

    # new_comment — scope to a specific video, else channel-wide
    video_id: str = ""

    # new_video — choose source + which channel to watch
    video_source: str = "own"  # "own" or "rss"
    watched_channel_id: str = ""

    # new_video_search_match
    search_query: str = ""

    max_per_poll: int = 25
    poll_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS

    @field_validator(
        "video_id",
        "watched_channel_id",
        mode="before",
    )
    @classmethod
    def _coerce_resource_id(cls, value: Any) -> str:
        if isinstance(value, dict):
            v = value.get("id")
            return str(v) if isinstance(v, str) else ""
        return str(value) if value is not None else ""

    @field_validator("event_type", mode="before")
    @classmethod
    def _coerce_event_type(cls, value: Any) -> str:
        v = str(value or "").strip().lower()
        return v if v in EVENT_TYPES else EVENT_NEW_COMMENT


class GoogleYouTubeTriggerNode(BaseNode[GoogleYouTubeTriggerProperties]):
    @classmethod
    def get_properties_model(cls):
        return GoogleYouTubeTriggerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.gyt_change",
            name=NAME,
            category="trigger",
            description=(
                "Fires on new comments, new subscribers, new uploads, search "
                "matches, or replies to your comments. First poll snapshots "
                "silently; later polls emit one execution per new item. "
                "Quota-aware — `new_video` for other channels uses YouTube's "
                "RSS feed (zero quota)."
            ),
            icon=ICON_SLUG,
            color=COLOR,
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
                    "default": EVENT_NEW_COMMENT,
                    "options": [
                        {"label": "New comment on my channel / video", "value": EVENT_NEW_COMMENT},
                        {"label": "New subscriber on my channel", "value": EVENT_NEW_SUBSCRIBER},
                        {
                            "label": "New video uploaded (own or watched channel)",
                            "value": EVENT_NEW_VIDEO,
                        },
                        {"label": "New video matching search query", "value": EVENT_SEARCH_MATCH},
                        {"label": "New reply to my comment", "value": EVENT_REPLY_TO_MY_COMMENT},
                    ],
                },
                # new_comment — optional video filter
                {
                    "name": "video_id",
                    "label": "Video (optional)",
                    "type": "youtube-video",
                    "description": "Leave blank to watch every comment thread on your channel.",
                    "condition": {"field": "event_type", "value": EVENT_NEW_COMMENT},
                    "mode": "advanced",
                },
                # new_video — source picker
                {
                    "name": "video_source",
                    "label": "Source",
                    "type": "options",
                    "default": "own",
                    "options": _VIDEO_SOURCE_OPTIONS,
                    "condition": {"field": "event_type", "value": EVENT_NEW_VIDEO},
                },
                {
                    "name": "watched_channel_id",
                    "label": "Channel ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "UC… (channel ID, not @handle)",
                    "description": "Paste the channel's `UC…` id (not the @handle).",
                    "condition": {
                        "all": [
                            {"field": "event_type", "value": EVENT_NEW_VIDEO},
                            {"field": "video_source", "value": "rss"},
                        ]
                    },
                },
                # search_match
                {
                    "name": "search_query",
                    "label": "Search query",
                    "type": "string",
                    "required": True,
                    "placeholder": "workflow automation tutorial",
                    "description": (
                        "Each poll costs 100 quota units — keep the interval above 5 minutes."
                    ),
                    "condition": {"field": "event_type", "value": EVENT_SEARCH_MATCH},
                },
                # shared
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
                    "description": "Min 30s. Bump to 300+ for `new_video_search_match`.",
                    "mode": "advanced",
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "id", "type": "string"},
                {"label": "title", "type": "string"},
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
        if (
            isinstance(input_data, dict)
            and input_data.get("id")
            and input_data.get("event_type") in EVENT_TYPES
        ):
            return NodeResult(success=True, output_data=input_data)

        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="Google OAuth credential required.")

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
            return NodeResult(
                success=False,
                error=f"YouTube API error {exc.response.status_code}: {exc.response.text[:200]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("GoogleYouTubeTriggerNode poll failed: %s", exc, exc_info=True)
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
                    "items": [],
                    **_cursor_summary(new_cursor),
                },
                handled_successors=True,
            )
        return NodeResult(success=True, output_data=matches[0])

    async def poll(
        self, token: str, cursor: dict[str, Any] | None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        headers = {"Authorization": f"Bearer {token}"}
        event_type = self.props.event_type
        prior_event = (cursor or {}).get("event_type")
        if cursor and prior_event != event_type:
            cursor = None

        if event_type == EVENT_NEW_COMMENT:
            return await self._poll_new_comment(headers, cursor)
        if event_type == EVENT_NEW_SUBSCRIBER:
            return await self._poll_new_subscriber(headers, cursor)
        if event_type == EVENT_NEW_VIDEO:
            return await self._poll_new_video(headers, cursor)
        if event_type == EVENT_SEARCH_MATCH:
            return await self._poll_search_match(headers, cursor)
        if event_type == EVENT_REPLY_TO_MY_COMMENT:
            return await self._poll_replies_to_me(headers, cursor)
        return [], {"event_type": event_type}

    # ── per-event pollers ─────────────────────────────────────────────

    async def _poll_new_comment(
        self, headers: dict[str, str], cursor: dict[str, Any] | None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        params: dict[str, Any] = {
            "part": "snippet,replies",
            "order": "time",
            "maxResults": min(100, max(1, int(self.props.max_per_poll or 25) * 2)),
        }
        if self.props.video_id:
            params["videoId"] = self.props.video_id
        else:
            params["allThreadsRelatedToChannelId"] = await self._own_channel_id(headers)
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{YT_API}/commentThreads", headers=headers, params=params)
            r.raise_for_status()
            threads = r.json().get("items") or []

        max_per_poll = max(1, min(int(self.props.max_per_poll or 25), 500))
        ids_now = [str(t.get("id")) for t in threads if t.get("id")]
        prior_ids = (cursor or {}).get("known_ids")
        if not isinstance(prior_ids, list):
            return [], {"event_type": EVENT_NEW_COMMENT, "known_ids": ids_now}

        known = set(prior_ids)
        matches: list[dict[str, Any]] = []
        emitted: set[str] = set()
        for thread in threads:
            tid = str(thread.get("id") or "")
            if not tid or tid in known:
                continue
            matches.append({**_flatten_comment(thread), "event_type": EVENT_NEW_COMMENT})
            emitted.add(tid)
            if len(matches) >= max_per_poll:
                break
        return matches, {
            "event_type": EVENT_NEW_COMMENT,
            "known_ids": list(known | emitted),
        }

    async def _poll_new_subscriber(
        self, headers: dict[str, str], cursor: dict[str, Any] | None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        params: dict[str, Any] = {
            "part": "snippet,subscriberSnippet",
            "mySubscribers": "true",
            "maxResults": 50,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{YT_API}/subscriptions", headers=headers, params=params)
            r.raise_for_status()
            subs = r.json().get("items") or []

        max_per_poll = max(1, min(int(self.props.max_per_poll or 25), 500))
        ids_now = [str(s.get("id")) for s in subs if s.get("id")]
        prior_ids = (cursor or {}).get("known_ids")
        if not isinstance(prior_ids, list):
            return [], {"event_type": EVENT_NEW_SUBSCRIBER, "known_ids": ids_now}

        known = set(prior_ids)
        matches: list[dict[str, Any]] = []
        emitted: set[str] = set()
        for sub in subs:
            sid = str(sub.get("id") or "")
            if not sid or sid in known:
                continue
            matches.append({**_flatten_subscription(sub), "event_type": EVENT_NEW_SUBSCRIBER})
            emitted.add(sid)
            if len(matches) >= max_per_poll:
                break
        return matches, {
            "event_type": EVENT_NEW_SUBSCRIBER,
            "known_ids": list(known | emitted),
        }

    async def _poll_new_video(
        self, headers: dict[str, str], cursor: dict[str, Any] | None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        source = self.props.video_source or "own"
        if source == "rss":
            return await self._poll_new_video_rss(cursor)

        # API path — own channel.
        async with httpx.AsyncClient(timeout=30) as client:
            ch = await client.get(
                f"{YT_API}/channels",
                headers=headers,
                params={"part": "contentDetails", "mine": "true"},
            )
            ch.raise_for_status()
            items = ch.json().get("items") or []
            if not items:
                return [], {"event_type": EVENT_NEW_VIDEO, "known_ids": []}
            uploads = ((items[0].get("contentDetails") or {}).get("relatedPlaylists") or {}).get(
                "uploads"
            ) or ""
            if not uploads:
                return [], {"event_type": EVENT_NEW_VIDEO, "known_ids": []}
            pl = await client.get(
                f"{YT_API}/playlistItems",
                headers=headers,
                params={
                    "part": "contentDetails,snippet",
                    "playlistId": uploads,
                    "maxResults": 50,
                },
            )
            pl.raise_for_status()
            api_items = pl.json().get("items") or []

        max_per_poll = max(1, min(int(self.props.max_per_poll or 25), 500))
        videos_now = [(i.get("contentDetails") or {}).get("videoId") for i in api_items]
        videos_now = [v for v in videos_now if v]
        prior_ids = (cursor or {}).get("known_ids")
        if not isinstance(prior_ids, list):
            return [], {"event_type": EVENT_NEW_VIDEO, "known_ids": videos_now}

        known = set(prior_ids)
        matches: list[dict[str, Any]] = []
        emitted: set[str] = set()
        for item in api_items:
            vid = (item.get("contentDetails") or {}).get("videoId")
            if not vid or vid in known:
                continue
            matches.append(
                {
                    **_flatten_video({"id": vid, "snippet": item.get("snippet") or {}}),
                    "event_type": EVENT_NEW_VIDEO,
                    "source": "own",
                }
            )
            emitted.add(vid)
            if len(matches) >= max_per_poll:
                break
        return matches, {
            "event_type": EVENT_NEW_VIDEO,
            "known_ids": list(known | emitted),
        }

    async def _poll_new_video_rss(
        self, cursor: dict[str, Any] | None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        cid = self.props.watched_channel_id
        if not cid:
            return [], {"event_type": EVENT_NEW_VIDEO, "known_ids": []}
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(channel_feed_url(cid))
            r.raise_for_status()
            videos = parse_feed(r.content)

        max_per_poll = max(1, min(int(self.props.max_per_poll or 25), 500))
        ids_now = [v["video_id"] for v in videos]
        prior_ids = (cursor or {}).get("known_ids")
        if not isinstance(prior_ids, list):
            return [], {"event_type": EVENT_NEW_VIDEO, "known_ids": ids_now}

        known = set(prior_ids)
        matches: list[dict[str, Any]] = []
        emitted: set[str] = set()
        for v in videos:
            vid = v["video_id"]
            if vid in known:
                continue
            matches.append(
                {
                    "id": vid,
                    "title": v["title"],
                    "channel_id": v["channel_id"],
                    "channel_title": v["channel_title"],
                    "published_at": v["published_at"],
                    "url": v["url"],
                    "event_type": EVENT_NEW_VIDEO,
                    "source": "rss",
                }
            )
            emitted.add(vid)
            if len(matches) >= max_per_poll:
                break
        return matches, {
            "event_type": EVENT_NEW_VIDEO,
            "known_ids": list(known | emitted),
        }

    async def _poll_search_match(
        self, headers: dict[str, str], cursor: dict[str, Any] | None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        query = (self.props.search_query or "").strip()
        if not query:
            return [], {"event_type": EVENT_SEARCH_MATCH, "last_published_at": ""}

        params: dict[str, Any] = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "order": "date",
            "maxResults": max(1, min(int(self.props.max_per_poll or 25), 50)),
        }
        last = (cursor or {}).get("last_published_at")
        if last:
            params["publishedAfter"] = last

        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{YT_API}/search", headers=headers, params=params)
            r.raise_for_status()
            items = r.json().get("items") or []

        if not last:
            newest = max(
                ((i.get("snippet") or {}).get("publishedAt") or "" for i in items),
                default="",
            )
            return [], {
                "event_type": EVENT_SEARCH_MATCH,
                "last_published_at": newest or _utc_now_rfc3339(),
            }

        # Emit oldest first so workflow order matches publish order.
        items.sort(key=lambda i: (i.get("snippet") or {}).get("publishedAt") or "")
        matches = [{**_flatten_video(item), "event_type": EVENT_SEARCH_MATCH} for item in items]
        new_last = (items[-1].get("snippet", {}).get("publishedAt") if items else last) or last
        return matches, {
            "event_type": EVENT_SEARCH_MATCH,
            "last_published_at": new_last,
        }

    async def _poll_replies_to_me(
        self, headers: dict[str, str], cursor: dict[str, Any] | None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Walk recent threads on the user's channel, pull replies under
        any thread the user authored, and emit those that are new since
        last cursor."""
        own_channel = await self._own_channel_id(headers)
        if not own_channel:
            return [], {"event_type": EVENT_REPLY_TO_MY_COMMENT, "known_ids": []}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{YT_API}/commentThreads",
                headers=headers,
                params={
                    "part": "snippet,replies",
                    "allThreadsRelatedToChannelId": own_channel,
                    "order": "time",
                    "maxResults": 100,
                },
            )
            r.raise_for_status()
            threads = r.json().get("items") or []

        # Collect reply ids on threads I authored.
        new_replies: list[dict[str, Any]] = []
        for thread in threads:
            top = (thread.get("snippet") or {}).get("topLevelComment") or {}
            author_chan = ((top.get("snippet") or {}).get("authorChannelId") or {}).get(
                "value"
            ) or ""
            if author_chan != own_channel:
                continue
            for reply in (thread.get("replies") or {}).get("comments") or []:
                new_replies.append(reply)

        max_per_poll = max(1, min(int(self.props.max_per_poll or 25), 500))
        ids_now = [str(r.get("id")) for r in new_replies if r.get("id")]
        prior_ids = (cursor or {}).get("known_ids")
        if not isinstance(prior_ids, list):
            return [], {
                "event_type": EVENT_REPLY_TO_MY_COMMENT,
                "known_ids": ids_now,
            }

        known = set(prior_ids)
        matches: list[dict[str, Any]] = []
        emitted: set[str] = set()
        for reply in new_replies:
            rid = str(reply.get("id") or "")
            if not rid or rid in known:
                continue
            matches.append(
                {
                    **_flatten_comment(reply),
                    "event_type": EVENT_REPLY_TO_MY_COMMENT,
                }
            )
            emitted.add(rid)
            if len(matches) >= max_per_poll:
                break
        return matches, {
            "event_type": EVENT_REPLY_TO_MY_COMMENT,
            "known_ids": list(known | emitted),
        }

    # ── shared helpers ────────────────────────────────────────────────

    async def _own_channel_id(self, headers: dict[str, str]) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{YT_API}/channels",
                headers=headers,
                params={"part": "id", "mine": "true"},
            )
            r.raise_for_status()
            items = r.json().get("items") or []
            return str(items[0].get("id") or "") if items else ""

    async def _stateless_preview(self, token: str) -> NodeResult:
        """Listen / preview path — emit the most recent matching item
        without persisting a cursor."""
        # For preview we just run the normal poller once; the resulting
        # cursor is discarded by the caller.
        matches, _ = await self.poll(token, None)
        if not matches:
            # First-poll snapshot returns no matches — pull a real preview
            # one by reading the first item from the source.
            matches, _ = await self.poll(token, {"event_type": self.props.event_type})
        if not matches:
            return NodeResult(
                success=True,
                output_data={"matched": 0, "event_type": self.props.event_type},
                handled_successors=True,
            )
        return NodeResult(success=True, output_data=matches[0])


# ── module helpers ──────────────────────────────────────────────────────


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


def _utc_now_rfc3339() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _cursor_summary(cursor: dict[str, Any]) -> dict[str, Any]:
    event = cursor.get("event_type") or EVENT_NEW_COMMENT
    if event == EVENT_SEARCH_MATCH:
        return {
            "event_type": event,
            "last_published_at": cursor.get("last_published_at"),
        }
    return {"event_type": event, "tracked_ids": len(cursor.get("known_ids") or [])}


# ── scheduler integration ──────────────────────────────────────────────


async def _poll_for_scheduler(
    token: str,
    cursor: dict[str, Any] | None,
    props: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    node = GoogleYouTubeTriggerNode.__new__(GoogleYouTubeTriggerNode)
    node.props = GoogleYouTubeTriggerProperties(
        credential=None,
        event_type=str(props.get("event_type") or EVENT_NEW_COMMENT),
        video_id=props.get("video_id") or "",
        video_source=str(props.get("video_source") or "own"),
        watched_channel_id=str(props.get("watched_channel_id") or ""),
        search_query=str(props.get("search_query") or ""),
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
        node_type="trigger.gyt_change",
        provider=PROVIDER,
        poller=_poll_for_scheduler,
    )


_register()
