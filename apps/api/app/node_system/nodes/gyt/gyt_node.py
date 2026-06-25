"""YouTube action node — 28 ops via the Data API v3.

Videos
  - `list_my_videos` / `get_video` / `get_video_rating`
  - `upload_video`   / `update_video` / `delete_video`
  - `rate_video`     / `set_video_thumbnail`
  - `search_videos`

Playlists & playlist items
  - `list_playlists`     / `list_playlist_items`
  - `create_playlist`    / `update_playlist`    / `delete_playlist`
  - `add_video_to_playlist` / `remove_video_from_playlist`

Comments
  - `list_comments`   (top threads w/ replies)
  - `post_top_comment` / `reply_to_comment`
  - `update_comment`   / `delete_comment`
  - `mark_comment_as_spam` / `set_comment_moderation_status`

Channels
  - `get_my_channel` / `get_channel_by_id`

Subscriptions
  - `list_subscriptions` / `subscribe_to_channel` / `unsubscribe_from_channel`

OAuth scopes: `youtube.force-ssl` + `youtube.upload` (in
GoogleOAuthProvider).
"""

from __future__ import annotations

import re
from typing import Any

import httpx
from pydantic import BaseModel, field_validator

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

YT_API = "https://www.googleapis.com/youtube/v3"
YT_UPLOAD_API = "https://www.googleapis.com/upload/youtube/v3"


_PRIVACY_OPTIONS: list[dict[str, str]] = [
    {"label": "Public", "value": "public"},
    {"label": "Unlisted", "value": "unlisted"},
    {"label": "Private", "value": "private"},
]


_RATING_OPTIONS: list[dict[str, str]] = [
    {"label": "Like", "value": "like"},
    {"label": "Dislike", "value": "dislike"},
    {"label": "None (clear)", "value": "none"},
]


_MODERATION_STATUS_OPTIONS: list[dict[str, str]] = [
    {"label": "Held for review", "value": "heldForReview"},
    {"label": "Published", "value": "published"},
    {"label": "Rejected", "value": "rejected"},
]


_SEARCH_ORDER_OPTIONS: list[dict[str, str]] = [
    {"label": "Relevance", "value": "relevance"},
    {"label": "Date (newest)", "value": "date"},
    {"label": "View count", "value": "viewCount"},
    {"label": "Rating", "value": "rating"},
    {"label": "Title", "value": "title"},
]


_DURATION_OPTIONS: list[dict[str, str]] = [
    {"label": "Any", "value": "any"},
    {"label": "Short (< 4 min)", "value": "short"},
    {"label": "Medium (4–20 min)", "value": "medium"},
    {"label": "Long (> 20 min)", "value": "long"},
]


class GoogleYouTubeProperties(BaseModel):
    credential: str | None = None
    operation: str = "list_my_videos"

    # video identity
    video_id: str | None = None
    channel_id: str | None = None
    playlist_id: str | None = None
    playlist_item_id: str | None = None
    comment_id: str | None = None
    subscription_id: str | None = None

    # upload / update video — metadata
    title: str | None = None
    description: Any = None  # accept template-rendered values
    tags: Any = None  # list[str]
    category_id: str = "22"  # 22 = People & Blogs (default)
    privacy: str = "private"
    made_for_kids: bool = False

    # media — upload_video / set_video_thumbnail
    media: Any = None  # MediaRenderer field

    # rate_video
    rating: str = "like"  # like / dislike / none

    # search_videos
    query: str | None = None
    published_after: str | None = None  # RFC3339
    published_before: str | None = None
    region_code: str = "US"
    duration_filter: str = "any"
    order: str = "relevance"
    max_results: int = 25
    page_token: str | None = None

    # comments
    comment_text: Any = None  # body of new/edited comment or reply
    parent_comment_id: str | None = None
    moderation_status: str = "published"
    ban_author: bool = False

    # subscribe
    target_channel_id: str | None = None

    # playlist CRUD
    playlist_title: str | None = None
    playlist_description: Any = None
    playlist_privacy: str = "private"

    # playlist items
    item_position: int | None = None  # zero-based insert position

    # list_playlist_items / list_comments
    page_size: int = 50

    # public video reads — accept full URL, short URL, or bare ID
    video_url_or_id: str | None = None
    # transcript language preference (BCP-47); falls back to auto-translated
    # or any available track if the preferred one is missing.
    transcript_language: str = "en"

    @field_validator(
        "video_id",
        "channel_id",
        "playlist_id",
        "playlist_item_id",
        "comment_id",
        "subscription_id",
        "target_channel_id",
        mode="before",
    )
    @classmethod
    def _coerce_resource_id(cls, value: Any) -> str | None:
        # Pickers emit `{id, title}` or `{id, name}` — collapse to id.
        if isinstance(value, dict):
            v = value.get("id")
            return str(v) if isinstance(v, str) and v else None
        if value in (None, ""):
            return None
        return str(value)


def _cond(op: str) -> dict[str, Any]:
    return {"field": "operation", "value": op}


def _cond_any(*ops: str) -> dict[str, Any]:
    return {"field": "operation", "value": list(ops)}


_VIDEO_PICKER_OPS = (
    "get_video",
    "get_video_rating",
    "update_video",
    "delete_video",
    "rate_video",
    "set_video_thumbnail",
    "list_comments",
    "post_top_comment",
    "add_video_to_playlist",
)

# Operations that read public-only data — no OAuth needed. The
# inspector hides the credential picker on these and `execute()` skips
# the access-token check.
_PUBLIC_OPS = ("get_public_video", "get_video_transcript")
_PLAYLIST_PICKER_OPS = (
    "update_playlist",
    "delete_playlist",
    "add_video_to_playlist",
    "list_playlist_items",
)
_CHANNEL_PICKER_OPS = ("get_channel_by_id", "subscribe_to_channel")
_VIDEO_METADATA_OPS = ("upload_video", "update_video")


class GoogleYouTubeNode(BaseNode[GoogleYouTubeProperties]):
    @classmethod
    def get_properties_model(cls):
        return GoogleYouTubeProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.gyt",
            name="YouTube",
            category="integration",
            description=(
                "Read, post, upload, and curate on YouTube — videos, comments, "
                "playlists, subscriptions, ratings, and thumbnails."
            ),
            icon="si:SiYoutube",
            color="#ff0000",
            properties=[
                {
                    "name": "credential",
                    "label": "Google Account",
                    "type": "credential",
                    "credentialType": "google_oauth",
                    "required": True,
                    # Public-read operations don't need OAuth — hide the
                    # picker so users can transcribe/summarise any
                    # YouTube video without signing in. The inspector
                    # treats the field as "not required" too because
                    # `shouldShowProperty` short-circuits validation
                    # when the condition hides it.
                    "condition": {
                        "field": "operation",
                        "operator": "notIn",
                        "value": list(_PUBLIC_OPS),
                    },
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "list_my_videos",
                    "options": [
                        {
                            "label": "Get Public Video (no auth)",
                            "value": "get_public_video",
                        },
                        {
                            "label": "Get Video Transcript (no auth)",
                            "value": "get_video_transcript",
                        },
                        {"label": "List My Videos", "value": "list_my_videos"},
                        {"label": "Get Video", "value": "get_video"},
                        {"label": "Get Video Rating", "value": "get_video_rating"},
                        {"label": "Upload Video", "value": "upload_video"},
                        {"label": "Update Video", "value": "update_video"},
                        {"label": "Delete Video", "value": "delete_video"},
                        {"label": "Rate Video (Like/Dislike)", "value": "rate_video"},
                        {"label": "Set Video Thumbnail", "value": "set_video_thumbnail"},
                        {"label": "Search Videos", "value": "search_videos"},
                        {"label": "List Playlists", "value": "list_playlists"},
                        {"label": "Create Playlist", "value": "create_playlist"},
                        {"label": "Update Playlist", "value": "update_playlist"},
                        {"label": "Delete Playlist", "value": "delete_playlist"},
                        {"label": "Add Video to Playlist", "value": "add_video_to_playlist"},
                        {
                            "label": "Remove Video from Playlist",
                            "value": "remove_video_from_playlist",
                        },
                        {"label": "List Playlist Items", "value": "list_playlist_items"},
                        {"label": "List Comments on a Video", "value": "list_comments"},
                        {"label": "Post Top-Level Comment", "value": "post_top_comment"},
                        {"label": "Reply to a Comment", "value": "reply_to_comment"},
                        {"label": "Update My Comment", "value": "update_comment"},
                        {"label": "Delete My Comment", "value": "delete_comment"},
                        {"label": "Mark Comment as Spam", "value": "mark_comment_as_spam"},
                        {"label": "Moderate Comment", "value": "set_comment_moderation_status"},
                        {"label": "Get My Channel", "value": "get_my_channel"},
                        {"label": "Get Channel by ID", "value": "get_channel_by_id"},
                        {"label": "List Subscriptions", "value": "list_subscriptions"},
                        {"label": "Subscribe to Channel", "value": "subscribe_to_channel"},
                        {
                            "label": "Unsubscribe (by subscription ID)",
                            "value": "unsubscribe_from_channel",
                        },
                    ],
                },
                # ── public video — URL or bare ID ──────────────────────
                {
                    "name": "video_url_or_id",
                    "label": "Video URL or ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    "description": (
                        "Paste a YouTube URL (regular, shorts, or youtu.be) or "
                        "just the 11-character video ID. No sign-in required."
                    ),
                    "condition": _cond_any(*_PUBLIC_OPS),
                },
                {
                    "name": "transcript_language",
                    "label": "Transcript language",
                    "type": "string",
                    "default": "en",
                    "description": (
                        "BCP-47 code (en, es, fr…). Falls back to any "
                        "available track if the preferred one is missing."
                    ),
                    "condition": _cond("get_video_transcript"),
                    "mode": "advanced",
                },
                # ── video picker ───────────────────────────────────────
                {
                    "name": "video_id",
                    "label": "Video",
                    "type": "youtube-video",
                    "required": True,
                    "condition": _cond_any(*_VIDEO_PICKER_OPS),
                },
                # ── playlist picker ────────────────────────────────────
                {
                    "name": "playlist_id",
                    "label": "Playlist",
                    "type": "youtube-playlist",
                    "required": True,
                    "condition": _cond_any(*_PLAYLIST_PICKER_OPS),
                },
                # ── channel picker ─────────────────────────────────────
                {
                    "name": "channel_id",
                    "label": "Channel",
                    "type": "youtube-channel",
                    "required": True,
                    "condition": _cond_any(*_CHANNEL_PICKER_OPS),
                },
                # ── upload_video / update_video — metadata ─────────────
                {
                    "name": "title",
                    "label": "Title",
                    "type": "string",
                    "required": True,
                    "placeholder": "My new video",
                    "condition": _cond_any(
                        *_VIDEO_METADATA_OPS, "create_playlist", "update_playlist"
                    ),
                },
                {
                    "name": "description",
                    "label": "Description",
                    "type": "string",
                    "typeOptions": {"multiline": True, "rows": 4},
                    "condition": _cond_any(
                        *_VIDEO_METADATA_OPS, "create_playlist", "update_playlist"
                    ),
                },
                {
                    "name": "tags",
                    "label": "Tags",
                    "type": "json",
                    "placeholder": '["tutorial", "workflow"]',
                    "condition": _cond_any(*_VIDEO_METADATA_OPS),
                    "mode": "advanced",
                },
                {
                    "name": "category_id",
                    "label": "Category ID",
                    "type": "string",
                    "default": "22",
                    "description": "YouTube videoCategoryId — 22 = People & Blogs, 27 = Education, 28 = Tech.",
                    "condition": _cond_any(*_VIDEO_METADATA_OPS),
                    "mode": "advanced",
                },
                {
                    "name": "privacy",
                    "label": "Privacy",
                    "type": "options",
                    "default": "private",
                    "options": _PRIVACY_OPTIONS,
                    "condition": _cond_any(*_VIDEO_METADATA_OPS),
                },
                {
                    "name": "made_for_kids",
                    "label": "Made for kids",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond_any(*_VIDEO_METADATA_OPS),
                    "mode": "advanced",
                },
                {
                    "name": "media",
                    "label": "Video file",
                    "type": "media",
                    "required": True,
                    "typeOptions": {"accept": "video/*"},
                    "description": "Upload from URL, drop a file, or pick from your Library. Up to ~500MB single-chunk.",
                    "condition": _cond("upload_video"),
                },
                {
                    "name": "media",
                    "label": "Thumbnail image",
                    "type": "media",
                    "required": True,
                    "typeOptions": {"accept": "image/*"},
                    "description": "JPEG / PNG, ≤ 2MB, 16:9 recommended.",
                    "condition": _cond("set_video_thumbnail"),
                },
                # ── rate_video ─────────────────────────────────────────
                {
                    "name": "rating",
                    "label": "Rating",
                    "type": "options",
                    "default": "like",
                    "options": _RATING_OPTIONS,
                    "condition": _cond("rate_video"),
                },
                # ── search_videos ──────────────────────────────────────
                {
                    "name": "query",
                    "label": "Search query",
                    "type": "string",
                    "required": True,
                    "placeholder": "workflow automation tutorial",
                    "condition": _cond("search_videos"),
                },
                {
                    "name": "published_after",
                    "label": "Published after",
                    "type": "datetime",
                    "typeOptions": {"granularity": "datetime"},
                    "condition": _cond("search_videos"),
                    "mode": "advanced",
                },
                {
                    "name": "published_before",
                    "label": "Published before",
                    "type": "datetime",
                    "typeOptions": {"granularity": "datetime"},
                    "condition": _cond("search_videos"),
                    "mode": "advanced",
                },
                {
                    "name": "region_code",
                    "label": "Region code",
                    "type": "string",
                    "default": "US",
                    "description": "ISO 3166-1 alpha-2 country code.",
                    "condition": _cond("search_videos"),
                    "mode": "advanced",
                },
                {
                    "name": "duration_filter",
                    "label": "Duration",
                    "type": "options",
                    "default": "any",
                    "options": _DURATION_OPTIONS,
                    "condition": _cond("search_videos"),
                    "mode": "advanced",
                },
                {
                    "name": "order",
                    "label": "Sort order",
                    "type": "options",
                    "default": "relevance",
                    "options": _SEARCH_ORDER_OPTIONS,
                    "condition": _cond("search_videos"),
                },
                # ── comments ───────────────────────────────────────────
                {
                    "name": "comment_text",
                    "label": "Comment text",
                    "type": "string",
                    "required": True,
                    "typeOptions": {"multiline": True, "rows": 3},
                    "placeholder": "Nice video!",
                    "condition": _cond_any(
                        "post_top_comment",
                        "reply_to_comment",
                        "update_comment",
                    ),
                },
                {
                    "name": "parent_comment_id",
                    "label": "Parent comment ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $trigger.comment_id }}",
                    "condition": _cond("reply_to_comment"),
                },
                {
                    "name": "comment_id",
                    "label": "Comment ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $trigger.comment_id }}",
                    "condition": _cond_any(
                        "update_comment",
                        "delete_comment",
                        "mark_comment_as_spam",
                        "set_comment_moderation_status",
                    ),
                },
                {
                    "name": "moderation_status",
                    "label": "Status",
                    "type": "options",
                    "default": "published",
                    "options": _MODERATION_STATUS_OPTIONS,
                    "condition": _cond("set_comment_moderation_status"),
                },
                {
                    "name": "ban_author",
                    "label": "Ban author",
                    "type": "boolean",
                    "default": False,
                    "description": "When rejecting, also block this user from commenting on your channel.",
                    "condition": _cond("set_comment_moderation_status"),
                    "mode": "advanced",
                },
                # ── playlist CRUD ──────────────────────────────────────
                {
                    "name": "playlist_privacy",
                    "label": "Playlist privacy",
                    "type": "options",
                    "default": "private",
                    "options": _PRIVACY_OPTIONS,
                    "condition": _cond_any("create_playlist", "update_playlist"),
                },
                # ── playlist items ─────────────────────────────────────
                {
                    "name": "item_position",
                    "label": "Position (0-based)",
                    "type": "number",
                    "description": "Leave blank to append.",
                    "condition": _cond("add_video_to_playlist"),
                    "mode": "advanced",
                },
                {
                    "name": "playlist_item_id",
                    "label": "Playlist item ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $trigger.playlist_item_id }}",
                    "condition": _cond("remove_video_from_playlist"),
                },
                # ── subscriptions ──────────────────────────────────────
                {
                    "name": "target_channel_id",
                    "label": "Channel to subscribe to",
                    "type": "youtube-channel",
                    "required": True,
                    "condition": _cond("subscribe_to_channel"),
                },
                {
                    "name": "subscription_id",
                    "label": "Subscription ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "Pass the subscription id from list_subscriptions output.",
                    "condition": _cond("unsubscribe_from_channel"),
                },
                # ── listing ────────────────────────────────────────────
                {
                    "name": "max_results",
                    "label": "Max results",
                    "type": "number",
                    "default": 25,
                    "condition": _cond_any(
                        "search_videos",
                        "list_subscriptions",
                        "list_my_videos",
                    ),
                    "mode": "advanced",
                },
                {
                    "name": "page_size",
                    "label": "Page size",
                    "type": "number",
                    "default": 50,
                    "condition": _cond_any(
                        "list_playlists",
                        "list_playlist_items",
                        "list_comments",
                    ),
                    "mode": "advanced",
                },
                {
                    "name": "page_token",
                    "label": "Page token",
                    "type": "string",
                    "placeholder": "Continuation token from a prior call",
                    "condition": _cond_any(
                        "search_videos",
                        "list_playlists",
                        "list_playlist_items",
                        "list_comments",
                        "list_subscriptions",
                        "list_my_videos",
                    ),
                    "mode": "advanced",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "id", "type": "string"},
                {"label": "title", "type": "string"},
                {"label": "channel_title", "type": "string"},
                {"label": "url", "type": "string"},
            ],
            allow_error=True,
            credential_type="google_oauth",
        )

    def _get_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        op = self.props.operation
        handler = _HANDLERS.get(op)
        if handler is None:
            return NodeResult(success=False, error=f"Unknown operation: {op}")
        # Public ops bypass OAuth — they read youtube.com / oEmbed directly
        # and never call the authenticated Data API.
        if op in _PUBLIC_OPS:
            headers: dict[str, str] = {}
        else:
            token = self._get_token()
            if not token:
                return NodeResult(success=False, error="Google OAuth credential required.")
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                return await handler(self, client, headers)
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=f"YouTube API error {exc.response.status_code}: {exc.response.text[:300]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GoogleYouTubeNode {op} failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))


# ── flatteners (shared with trigger) ────────────────────────────────────


def _flatten_video(video: dict[str, Any]) -> dict[str, Any]:
    snippet = video.get("snippet") or {}
    statistics = video.get("statistics") or {}
    content = video.get("contentDetails") or {}
    thumbs = snippet.get("thumbnails") or {}
    # `high` is present on every video; fall back to lower res if missing.
    thumb = ((thumbs.get("maxres") or thumbs.get("high") or thumbs.get("default")) or {}).get(
        "url"
    ) or ""
    vid_id = video.get("id")
    if isinstance(vid_id, dict):
        # `search.list` returns `{kind, videoId}` as the id object.
        vid_id = vid_id.get("videoId")
    return {
        "id": vid_id,
        "title": snippet.get("title") or "",
        "description": snippet.get("description") or "",
        "channel_id": snippet.get("channelId") or "",
        "channel_title": snippet.get("channelTitle") or "",
        "published_at": snippet.get("publishedAt") or "",
        "thumbnail_url": thumb,
        "tags": snippet.get("tags") or [],
        "category_id": snippet.get("categoryId") or "",
        "duration": content.get("duration") or "",
        "view_count": int(statistics.get("viewCount") or 0),
        "like_count": int(statistics.get("likeCount") or 0),
        "comment_count": int(statistics.get("commentCount") or 0),
        "url": f"https://www.youtube.com/watch?v={vid_id}" if vid_id else "",
    }


def _flatten_comment(thread_or_comment: dict[str, Any]) -> dict[str, Any]:
    """Accepts either a commentThread (top-level) or a bare comment
    resource. Pulls the same fields out of both."""
    snip = thread_or_comment.get("snippet") or {}
    top = snip.get("topLevelComment") or thread_or_comment  # threads vs comments
    s = (top.get("snippet") or {}) if isinstance(top, dict) else {}
    if not s:
        s = snip
    return {
        "id": top.get("id") or thread_or_comment.get("id"),
        "video_id": s.get("videoId") or snip.get("videoId") or "",
        "author": s.get("authorDisplayName") or "",
        "author_channel_id": (s.get("authorChannelId") or {}).get("value") or "",
        "text": s.get("textOriginal") or s.get("textDisplay") or "",
        "published_at": s.get("publishedAt") or "",
        "updated_at": s.get("updatedAt") or "",
        "like_count": int(s.get("likeCount") or 0),
        "parent_id": s.get("parentId") or "",
        "can_reply": snip.get("canReply") if isinstance(snip, dict) else None,
        "total_reply_count": int(snip.get("totalReplyCount") or 0),
    }


def _flatten_subscription(sub: dict[str, Any]) -> dict[str, Any]:
    snippet = sub.get("snippet") or {}
    return {
        "id": sub.get("id"),
        "subscriber_channel_id": (snippet.get("resourceId") or {}).get("channelId") or "",
        "subscriber_title": snippet.get("title") or "",
        "subscriber_description": snippet.get("description") or "",
        "subscribed_at": snippet.get("publishedAt") or "",
        "thumbnail_url": ((snippet.get("thumbnails") or {}).get("default") or {}).get("url") or "",
    }


def _flatten_playlist(playlist: dict[str, Any]) -> dict[str, Any]:
    snippet = playlist.get("snippet") or {}
    content = playlist.get("contentDetails") or {}
    status = playlist.get("status") or {}
    return {
        "id": playlist.get("id"),
        "title": snippet.get("title") or "",
        "description": snippet.get("description") or "",
        "channel_id": snippet.get("channelId") or "",
        "channel_title": snippet.get("channelTitle") or "",
        "published_at": snippet.get("publishedAt") or "",
        "privacy": status.get("privacyStatus") or "",
        "item_count": int(content.get("itemCount") or 0),
    }


def _flatten_channel(channel: dict[str, Any]) -> dict[str, Any]:
    snippet = channel.get("snippet") or {}
    statistics = channel.get("statistics") or {}
    return {
        "id": channel.get("id"),
        "title": snippet.get("title") or "",
        "description": snippet.get("description") or "",
        "custom_url": snippet.get("customUrl") or "",
        "published_at": snippet.get("publishedAt") or "",
        "country": snippet.get("country") or "",
        "subscriber_count": int(statistics.get("subscriberCount") or 0),
        "video_count": int(statistics.get("videoCount") or 0),
        "view_count": int(statistics.get("viewCount") or 0),
        "thumbnail_url": ((snippet.get("thumbnails") or {}).get("default") or {}).get("url") or "",
    }


# ── helpers ─────────────────────────────────────────────────────────────


def _require_video(node: GoogleYouTubeNode) -> str | NodeResult:
    vid = (node.props.video_id or "").strip()
    if not vid:
        return NodeResult(success=False, error="Video is required.")
    return vid


def _require_playlist(node: GoogleYouTubeNode) -> str | NodeResult:
    pid = (node.props.playlist_id or "").strip()
    if not pid:
        return NodeResult(success=False, error="Playlist is required.")
    return pid


def _build_video_snippet(node: GoogleYouTubeNode) -> dict[str, Any]:
    snippet: dict[str, Any] = {}
    if node.props.title:
        snippet["title"] = node.props.title
    if node.props.description is not None and str(node.props.description) != "":
        snippet["description"] = str(node.props.description)
    if isinstance(node.props.tags, list):
        snippet["tags"] = [str(t) for t in node.props.tags if str(t).strip()]
    if node.props.category_id:
        snippet["categoryId"] = str(node.props.category_id)
    return snippet


def _build_status(node: GoogleYouTubeNode) -> dict[str, Any]:
    return {
        "privacyStatus": node.props.privacy or "private",
        "selfDeclaredMadeForKids": bool(node.props.made_for_kids),
    }


# ── handlers — videos ───────────────────────────────────────────────────


async def _list_my_videos(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    # YouTube has no `videos.list?mine=true` — we go through the user's
    # uploads playlist on their channel resource.
    ch = await client.get(
        f"{YT_API}/channels",
        headers=headers,
        params={"part": "contentDetails", "mine": "true"},
    )
    ch.raise_for_status()
    items = ch.json().get("items") or []
    if not items:
        return NodeResult(success=False, error="The signed-in account has no YouTube channel.")
    uploads_id = ((items[0].get("contentDetails") or {}).get("relatedPlaylists") or {}).get(
        "uploads"
    ) or ""
    if not uploads_id:
        return NodeResult(success=False, error="Uploads playlist not found.")

    params: dict[str, Any] = {
        "part": "contentDetails,snippet",
        "playlistId": uploads_id,
        "maxResults": max(1, min(int(node.props.max_results or 25), 50)),
    }
    if node.props.page_token:
        params["pageToken"] = node.props.page_token
    pl = await client.get(f"{YT_API}/playlistItems", headers=headers, params=params)
    pl.raise_for_status()
    plist = pl.json()
    video_ids = [
        ((i.get("contentDetails") or {}).get("videoId"))
        for i in (plist.get("items") or [])
        if (i.get("contentDetails") or {}).get("videoId")
    ]
    if not video_ids:
        return NodeResult(
            success=True,
            output_data={"videos": [], "next_page_token": plist.get("nextPageToken")},
        )
    # Hydrate full video resources for stats/thumbnails.
    detail = await client.get(
        f"{YT_API}/videos",
        headers=headers,
        params={
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(video_ids),
        },
    )
    detail.raise_for_status()
    videos = [_flatten_video(v) for v in (detail.json().get("items") or [])]
    return NodeResult(
        success=True,
        output_data={
            "videos": videos,
            "next_page_token": plist.get("nextPageToken"),
        },
    )


async def _get_video(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    vid = _require_video(node)
    if isinstance(vid, NodeResult):
        return vid
    r = await client.get(
        f"{YT_API}/videos",
        headers=headers,
        params={"part": "snippet,statistics,contentDetails,status", "id": vid},
    )
    r.raise_for_status()
    items = r.json().get("items") or []
    if not items:
        return NodeResult(success=False, error=f"Video {vid} not found.")
    return NodeResult(success=True, output_data=_flatten_video(items[0]))


async def _get_video_rating(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    vid = _require_video(node)
    if isinstance(vid, NodeResult):
        return vid
    r = await client.get(f"{YT_API}/videos/getRating", headers=headers, params={"id": vid})
    r.raise_for_status()
    items = r.json().get("items") or []
    if not items:
        return NodeResult(success=True, output_data={"video_id": vid, "rating": "none"})
    return NodeResult(
        success=True,
        output_data={"video_id": vid, "rating": items[0].get("rating") or "none"},
    )


async def _upload_video(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    from apps.api.app.node_system.nodes.meta._helpers import resolve_media_field

    if not node.props.title:
        return NodeResult(success=False, error="`title` is required.")
    media_url = resolve_media_field(node.props.media)
    if not media_url:
        return NodeResult(success=False, error="`media` could not be resolved to a fetchable URL.")

    # Pull bytes server-side. Single-chunk upload — good for ~500MB
    # files; larger needs the resumable session pattern.
    async with httpx.AsyncClient(timeout=600) as fetch:
        f_resp = await fetch.get(media_url)
        f_resp.raise_for_status()
        video_bytes = f_resp.content
        ct = f_resp.headers.get("content-type") or "video/*"

    metadata = {"snippet": _build_video_snippet(node), "status": _build_status(node)}
    files = {
        "metadata": ("metadata", _json_bytes(metadata), "application/json"),
        "video": ("upload", video_bytes, ct),
    }
    # `httpx` builds the multipart/related body automatically when we
    # hand it a `files=` dict.
    upload_headers = {"Authorization": headers["Authorization"]}
    r = await client.post(
        f"{YT_UPLOAD_API}/videos",
        headers=upload_headers,
        params={"part": "snippet,status", "uploadType": "multipart"},
        files=files,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=_flatten_video(r.json()))


def _json_bytes(payload: dict[str, Any]) -> bytes:
    import json as _json

    return _json.dumps(payload).encode("utf-8")


async def _update_video(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    vid = _require_video(node)
    if isinstance(vid, NodeResult):
        return vid
    snippet = _build_video_snippet(node)
    status = _build_status(node)
    if not snippet and not status:
        return NodeResult(success=False, error="Provide at least one field to update.")
    body: dict[str, Any] = {"id": vid}
    parts: list[str] = []
    if snippet:
        body["snippet"] = snippet
        parts.append("snippet")
    body["status"] = status
    parts.append("status")
    r = await client.put(
        f"{YT_API}/videos",
        headers=headers,
        json=body,
        params={"part": ",".join(parts)},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=_flatten_video(r.json()))


async def _delete_video(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    vid = _require_video(node)
    if isinstance(vid, NodeResult):
        return vid
    r = await client.delete(f"{YT_API}/videos", headers=headers, params={"id": vid})
    r.raise_for_status()
    return NodeResult(success=True, output_data={"id": vid, "deleted": True})


async def _rate_video(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    vid = _require_video(node)
    if isinstance(vid, NodeResult):
        return vid
    rating = node.props.rating or "like"
    r = await client.post(
        f"{YT_API}/videos/rate",
        headers=headers,
        params={"id": vid, "rating": rating},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data={"video_id": vid, "rating": rating})


async def _set_video_thumbnail(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    from apps.api.app.node_system.nodes.meta._helpers import resolve_media_field

    vid = _require_video(node)
    if isinstance(vid, NodeResult):
        return vid
    media_url = resolve_media_field(node.props.media)
    if not media_url:
        return NodeResult(success=False, error="`media` could not be resolved to a fetchable URL.")
    async with httpx.AsyncClient(timeout=60) as fetch:
        f_resp = await fetch.get(media_url)
        f_resp.raise_for_status()
        image_bytes = f_resp.content
        ct = f_resp.headers.get("content-type") or "image/jpeg"
    upload_headers = {
        "Authorization": headers["Authorization"],
        "Content-Type": ct,
    }
    r = await client.post(
        f"{YT_UPLOAD_API}/thumbnails/set",
        headers=upload_headers,
        params={"videoId": vid},
        content=image_bytes,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _search_videos(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    query = (node.props.query or "").strip()
    if not query:
        return NodeResult(success=False, error="`query` is required.")
    params: dict[str, Any] = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "regionCode": node.props.region_code or "US",
        "maxResults": max(1, min(int(node.props.max_results or 25), 50)),
        "order": node.props.order or "relevance",
        "videoDuration": node.props.duration_filter or "any",
    }
    if node.props.published_after:
        params["publishedAfter"] = node.props.published_after
    if node.props.published_before:
        params["publishedBefore"] = node.props.published_before
    if node.props.page_token:
        params["pageToken"] = node.props.page_token
    r = await client.get(f"{YT_API}/search", headers=headers, params=params)
    r.raise_for_status()
    data = r.json()
    videos = [_flatten_video(item) for item in (data.get("items") or [])]
    return NodeResult(
        success=True,
        output_data={
            "videos": videos,
            "next_page_token": data.get("nextPageToken"),
        },
    )


# ── handlers — playlists / items ────────────────────────────────────────


async def _list_playlists(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    params: dict[str, Any] = {
        "part": "snippet,contentDetails,status",
        "mine": "true",
        "maxResults": max(1, min(int(node.props.page_size or 50), 50)),
    }
    if node.props.page_token:
        params["pageToken"] = node.props.page_token
    r = await client.get(f"{YT_API}/playlists", headers=headers, params=params)
    r.raise_for_status()
    data = r.json()
    return NodeResult(
        success=True,
        output_data={
            "playlists": [_flatten_playlist(p) for p in (data.get("items") or [])],
            "next_page_token": data.get("nextPageToken"),
        },
    )


async def _create_playlist(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    title = (node.props.title or "").strip()
    if not title:
        return NodeResult(success=False, error="`title` is required.")
    body: dict[str, Any] = {
        "snippet": {"title": title},
        "status": {"privacyStatus": node.props.playlist_privacy or "private"},
    }
    if node.props.description is not None and str(node.props.description) != "":
        body["snippet"]["description"] = str(node.props.description)
    r = await client.post(
        f"{YT_API}/playlists",
        headers=headers,
        json=body,
        params={"part": "snippet,status"},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=_flatten_playlist(r.json()))


async def _update_playlist(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_playlist(node)
    if isinstance(pid, NodeResult):
        return pid
    body: dict[str, Any] = {"id": pid, "snippet": {}, "status": {}}
    if node.props.title:
        body["snippet"]["title"] = node.props.title
    if node.props.description is not None and str(node.props.description) != "":
        body["snippet"]["description"] = str(node.props.description)
    if not body["snippet"].get("title"):
        # `snippet.title` is required on update — read current to keep
        # it stable when the user only wanted to change description /
        # privacy.
        current = await client.get(
            f"{YT_API}/playlists",
            headers=headers,
            params={"id": pid, "part": "snippet"},
        )
        current.raise_for_status()
        items = current.json().get("items") or []
        if not items:
            return NodeResult(success=False, error=f"Playlist {pid} not found.")
        body["snippet"]["title"] = (items[0].get("snippet") or {}).get("title") or "Untitled"
    body["status"]["privacyStatus"] = node.props.playlist_privacy or "private"
    r = await client.put(
        f"{YT_API}/playlists",
        headers=headers,
        json=body,
        params={"part": "snippet,status"},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=_flatten_playlist(r.json()))


async def _delete_playlist(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_playlist(node)
    if isinstance(pid, NodeResult):
        return pid
    r = await client.delete(f"{YT_API}/playlists", headers=headers, params={"id": pid})
    r.raise_for_status()
    return NodeResult(success=True, output_data={"id": pid, "deleted": True})


async def _add_video_to_playlist(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_playlist(node)
    if isinstance(pid, NodeResult):
        return pid
    vid = _require_video(node)
    if isinstance(vid, NodeResult):
        return vid
    snippet: dict[str, Any] = {
        "playlistId": pid,
        "resourceId": {"kind": "youtube#video", "videoId": vid},
    }
    if node.props.item_position is not None:
        snippet["position"] = int(node.props.item_position)
    r = await client.post(
        f"{YT_API}/playlistItems",
        headers=headers,
        json={"snippet": snippet},
        params={"part": "snippet"},
    )
    r.raise_for_status()
    data = r.json()
    return NodeResult(
        success=True,
        output_data={
            "playlist_item_id": data.get("id"),
            "playlist_id": pid,
            "video_id": vid,
        },
    )


async def _remove_video_from_playlist(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    iid = (node.props.playlist_item_id or "").strip()
    if not iid:
        return NodeResult(success=False, error="`playlist_item_id` is required.")
    r = await client.delete(f"{YT_API}/playlistItems", headers=headers, params={"id": iid})
    r.raise_for_status()
    return NodeResult(success=True, output_data={"id": iid, "deleted": True})


async def _list_playlist_items(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_playlist(node)
    if isinstance(pid, NodeResult):
        return pid
    params: dict[str, Any] = {
        "part": "snippet,contentDetails",
        "playlistId": pid,
        "maxResults": max(1, min(int(node.props.page_size or 50), 50)),
    }
    if node.props.page_token:
        params["pageToken"] = node.props.page_token
    r = await client.get(f"{YT_API}/playlistItems", headers=headers, params=params)
    r.raise_for_status()
    data = r.json()
    items = [
        {
            "playlist_item_id": i.get("id"),
            "video_id": (i.get("contentDetails") or {}).get("videoId") or "",
            "position": (i.get("snippet") or {}).get("position") or 0,
            **_flatten_video(
                {
                    "id": (i.get("contentDetails") or {}).get("videoId"),
                    "snippet": i.get("snippet") or {},
                }
            ),
        }
        for i in (data.get("items") or [])
    ]
    return NodeResult(
        success=True,
        output_data={
            "items": items,
            "next_page_token": data.get("nextPageToken"),
        },
    )


# ── handlers — comments ────────────────────────────────────────────────


async def _list_comments(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    vid = _require_video(node)
    if isinstance(vid, NodeResult):
        return vid
    params: dict[str, Any] = {
        "part": "snippet,replies",
        "videoId": vid,
        "order": "time",
        "maxResults": max(1, min(int(node.props.page_size or 50), 100)),
    }
    if node.props.page_token:
        params["pageToken"] = node.props.page_token
    r = await client.get(f"{YT_API}/commentThreads", headers=headers, params=params)
    r.raise_for_status()
    data = r.json()
    threads: list[dict[str, Any]] = []
    for thread in data.get("items") or []:
        top = _flatten_comment(thread)
        replies = (thread.get("replies") or {}).get("comments") or []
        top["replies"] = [_flatten_comment(rp) for rp in replies]
        threads.append(top)
    return NodeResult(
        success=True,
        output_data={
            "comments": threads,
            "next_page_token": data.get("nextPageToken"),
        },
    )


async def _post_top_comment(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    vid = _require_video(node)
    if isinstance(vid, NodeResult):
        return vid
    text = "" if node.props.comment_text is None else str(node.props.comment_text)
    if not text.strip():
        return NodeResult(success=False, error="`comment_text` is required.")
    body = {
        "snippet": {
            "videoId": vid,
            "topLevelComment": {"snippet": {"textOriginal": text}},
        }
    }
    r = await client.post(
        f"{YT_API}/commentThreads",
        headers=headers,
        json=body,
        params={"part": "snippet"},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=_flatten_comment(r.json()))


async def _reply_to_comment(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = (node.props.parent_comment_id or "").strip()
    if not pid:
        return NodeResult(success=False, error="`parent_comment_id` is required.")
    text = "" if node.props.comment_text is None else str(node.props.comment_text)
    if not text.strip():
        return NodeResult(success=False, error="`comment_text` is required.")
    body = {"snippet": {"parentId": pid, "textOriginal": text}}
    r = await client.post(
        f"{YT_API}/comments",
        headers=headers,
        json=body,
        params={"part": "snippet"},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=_flatten_comment(r.json()))


async def _update_comment(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    cid = (node.props.comment_id or "").strip()
    if not cid:
        return NodeResult(success=False, error="`comment_id` is required.")
    text = "" if node.props.comment_text is None else str(node.props.comment_text)
    if not text.strip():
        return NodeResult(success=False, error="`comment_text` is required.")
    body = {"id": cid, "snippet": {"textOriginal": text}}
    r = await client.put(
        f"{YT_API}/comments",
        headers=headers,
        json=body,
        params={"part": "snippet"},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=_flatten_comment(r.json()))


async def _delete_comment(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    cid = (node.props.comment_id or "").strip()
    if not cid:
        return NodeResult(success=False, error="`comment_id` is required.")
    r = await client.delete(f"{YT_API}/comments", headers=headers, params={"id": cid})
    r.raise_for_status()
    return NodeResult(success=True, output_data={"id": cid, "deleted": True})


async def _mark_comment_as_spam(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    cid = (node.props.comment_id or "").strip()
    if not cid:
        return NodeResult(success=False, error="`comment_id` is required.")
    r = await client.post(f"{YT_API}/comments/markAsSpam", headers=headers, params={"id": cid})
    r.raise_for_status()
    return NodeResult(success=True, output_data={"id": cid, "marked_as_spam": True})


async def _set_comment_moderation_status(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    cid = (node.props.comment_id or "").strip()
    if not cid:
        return NodeResult(success=False, error="`comment_id` is required.")
    params = {
        "id": cid,
        "moderationStatus": node.props.moderation_status or "published",
        "banAuthor": "true" if node.props.ban_author else "false",
    }
    r = await client.post(f"{YT_API}/comments/setModerationStatus", headers=headers, params=params)
    r.raise_for_status()
    return NodeResult(
        success=True,
        output_data={
            "id": cid,
            "moderation_status": node.props.moderation_status,
        },
    )


# ── handlers — channels / subs ──────────────────────────────────────────


async def _get_my_channel(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    r = await client.get(
        f"{YT_API}/channels",
        headers=headers,
        params={"part": "snippet,statistics,contentDetails", "mine": "true"},
    )
    r.raise_for_status()
    items = r.json().get("items") or []
    if not items:
        return NodeResult(success=False, error="The signed-in account has no YouTube channel.")
    return NodeResult(success=True, output_data=_flatten_channel(items[0]))


async def _get_channel_by_id(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    cid = (node.props.channel_id or "").strip()
    if not cid:
        return NodeResult(success=False, error="`channel_id` is required.")
    r = await client.get(
        f"{YT_API}/channels",
        headers=headers,
        params={"part": "snippet,statistics", "id": cid},
    )
    r.raise_for_status()
    items = r.json().get("items") or []
    if not items:
        return NodeResult(success=False, error=f"Channel {cid} not found.")
    return NodeResult(success=True, output_data=_flatten_channel(items[0]))


async def _list_subscriptions(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    params: dict[str, Any] = {
        "part": "snippet",
        "mine": "true",
        "maxResults": max(1, min(int(node.props.max_results or 25), 50)),
    }
    if node.props.page_token:
        params["pageToken"] = node.props.page_token
    r = await client.get(f"{YT_API}/subscriptions", headers=headers, params=params)
    r.raise_for_status()
    data = r.json()
    return NodeResult(
        success=True,
        output_data={
            "subscriptions": [_flatten_subscription(s) for s in (data.get("items") or [])],
            "next_page_token": data.get("nextPageToken"),
        },
    )


async def _subscribe_to_channel(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    tcid = (node.props.target_channel_id or "").strip()
    if not tcid:
        return NodeResult(success=False, error="`target_channel_id` is required.")
    body = {"snippet": {"resourceId": {"kind": "youtube#channel", "channelId": tcid}}}
    r = await client.post(
        f"{YT_API}/subscriptions",
        headers=headers,
        json=body,
        params={"part": "snippet"},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=_flatten_subscription(r.json()))


async def _unsubscribe_from_channel(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = (node.props.subscription_id or "").strip()
    if not sid:
        return NodeResult(success=False, error="`subscription_id` is required.")
    r = await client.delete(f"{YT_API}/subscriptions", headers=headers, params={"id": sid})
    r.raise_for_status()
    return NodeResult(success=True, output_data={"id": sid, "deleted": True})


# ── public (no-auth) video helpers ────────────────────────────────────────

_YT_ID_RE = re.compile(r"(?:v=|youtu\.be/|/shorts/|/embed/)([A-Za-z0-9_-]{11})")


def _extract_video_id(raw: str | None) -> str | None:
    """Accept a YouTube URL (any common form) or a bare 11-char video ID,
    return the canonical video ID. Returns None if it can't parse one out
    of the input so the caller can produce a friendly error.
    """
    if not raw:
        return None
    s = raw.strip()
    # Bare ID — YouTube IDs are exactly 11 chars, [A-Za-z0-9_-].
    if len(s) == 11 and re.fullmatch(r"[A-Za-z0-9_-]{11}", s):
        return s
    m = _YT_ID_RE.search(s)
    return m.group(1) if m else None


async def _get_public_video(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    """Fetch public metadata for any video — no OAuth, no API key.

    Uses YouTube's oEmbed endpoint, which returns title, channel name,
    thumbnail, and (importantly) does NOT require authentication. Trade-off:
    no view count / duration / publish date. Callers who need those
    should reach for the authenticated `get_video` op instead.
    """
    vid = _extract_video_id(node.props.video_url_or_id)
    if not vid:
        return NodeResult(
            success=False,
            error="Could not parse a video ID out of `video_url_or_id`.",
        )
    watch_url = f"https://www.youtube.com/watch?v={vid}"
    r = await client.get(
        "https://www.youtube.com/oembed",
        params={"url": watch_url, "format": "json"},
    )
    if r.status_code == 404:
        return NodeResult(success=False, error=f"Video {vid} is unavailable or private.")
    r.raise_for_status()
    data = r.json()
    return NodeResult(
        success=True,
        output_data={
            "id": vid,
            "url": watch_url,
            "title": data.get("title"),
            "channel": {
                "name": data.get("author_name"),
                "url": data.get("author_url"),
            },
            "thumbnail": data.get("thumbnail_url"),
            "embed_html": data.get("html"),
            "width": data.get("width"),
            "height": data.get("height"),
        },
    )


async def _get_video_transcript(
    node: GoogleYouTubeNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    """Fetch captions for any public video. No OAuth required.

    Primary path: a RapidAPI YouTube-transcript provider, configured via
    ``RAPIDAPI_KEY`` + ``RAPIDAPI_YOUTUBE_TRANSCRIPT_HOST``. This works
    from cloud IPs because the proxy lives on RapidAPI's side, not
    youtube.com.

    Fallback: ``youtube-transcript-api`` direct scrape. Useful for local
    dev where the host IP isn't cloud-blocked. In production this
    typically fails with the ``YouTube is blocking requests from your
    IP`` error — when the RapidAPI path is configured, we never reach
    this fallback.
    """
    from apps.api.app.core.config import settings

    vid = _extract_video_id(node.props.video_url_or_id)
    if not vid:
        return NodeResult(
            success=False,
            error="Could not parse a video ID out of `video_url_or_id`.",
        )

    preferred = (node.props.transcript_language or "en").strip() or "en"

    if settings.RAPIDAPI_KEY and settings.RAPIDAPI_YOUTUBE_TRANSCRIPT_HOST:
        try:
            return await _fetch_transcript_via_rapidapi(vid, preferred, client)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "RapidAPI transcript fetch failed for %s; falling back to direct: %s",
                vid,
                exc,
            )

    return await _fetch_transcript_via_direct_scrape(vid, preferred)


async def _fetch_transcript_via_rapidapi(
    vid: str, preferred: str, client: httpx.AsyncClient
) -> NodeResult:
    """Hit the configured RapidAPI transcript endpoint.

    Different providers under the RapidAPI umbrella return slightly
    different JSON shapes (some list under ``transcript``, some under
    ``captions``, some under ``transcriptionAsText``). The shape probe
    here is intentionally tolerant — we look for the first plausible
    list-of-segments payload and project it into our canonical
    ``[{text, start, duration}]`` envelope.
    """
    from apps.api.app.core.config import settings

    host = settings.RAPIDAPI_YOUTUBE_TRANSCRIPT_HOST
    url = f"https://{host}/transcript"
    resp = await client.get(
        url,
        headers={
            "x-rapidapi-key": settings.RAPIDAPI_KEY,
            "x-rapidapi-host": host,
            "accept": "application/json",
        },
        params={"video_id": vid, "lang": preferred},
    )
    resp.raise_for_status()
    data = resp.json()

    segments = _coerce_rapidapi_segments(data)
    if segments is None:
        return NodeResult(
            success=False,
            error=(
                f"RapidAPI host {host} returned a payload we don't know how "
                "to parse. Check the provider's docs and confirm "
                "RAPIDAPI_YOUTUBE_TRANSCRIPT_HOST matches the one you subscribed to."
            ),
        )

    full_text = " ".join(seg["text"] for seg in segments).strip()
    language = _extract_rapidapi_language(data) or preferred
    return NodeResult(
        success=True,
        output_data={
            "id": vid,
            "language": language,
            "text": full_text,
            "segments": segments,
            "segment_count": len(segments),
            "source": "rapidapi",
        },
    )


def _coerce_rapidapi_segments(payload: Any) -> list[dict[str, Any]] | None:
    """Project a RapidAPI provider's payload into our canonical segments.

    Recognises a few common shapes:
        - ``[{text, start, duration}]``  (some providers)
        - ``{"transcript": [...]}``      (most common)
        - ``{"captions":  [...]}``       (older naming)
        - ``{"data":     [...]}``        (generic wrappers)
        - first element of a list of language-tracks, each with one of
          the above

    Each segment is normalised to ``{text: str, start: float, duration: float}``
    — missing fields default to 0.0 so downstream consumers don't
    crash on partial data.
    """

    def _to_segment(item: dict[str, Any]) -> dict[str, Any] | None:
        text = item.get("text") or item.get("subtitle") or item.get("snippet")
        if text is None:
            return None
        return {
            "text": str(text),
            "start": float(item.get("start") or item.get("offset") or 0.0),
            "duration": float(item.get("duration") or item.get("dur") or item.get("length") or 0.0),
        }

    def _try_list(maybe_list: Any) -> list[dict[str, Any]] | None:
        if not isinstance(maybe_list, list):
            return None
        segs: list[dict[str, Any]] = []
        for item in maybe_list:
            if isinstance(item, dict):
                s = _to_segment(item)
                if s is not None:
                    segs.append(s)
        return segs if segs else None

    direct = _try_list(payload)
    if direct is not None:
        return direct
    if isinstance(payload, dict):
        for key in ("transcript", "captions", "data", "segments", "transcriptionAsText"):
            if key not in payload:
                continue
            value = payload[key]
            if isinstance(value, str):
                return [{"text": value, "start": 0.0, "duration": 0.0}]
            attempt = _try_list(value)
            if attempt is not None:
                return attempt
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        # Some providers return a list of language-tracks. Take the
        # first one's transcript and try again.
        return _coerce_rapidapi_segments(payload[0])
    return None


def _extract_rapidapi_language(payload: Any) -> str | None:
    if isinstance(payload, dict):
        lang = payload.get("language") or payload.get("language_code") or payload.get("lang")
        if isinstance(lang, str) and lang:
            return lang
    return None


async def _fetch_transcript_via_direct_scrape(vid: str, preferred: str) -> NodeResult:
    """Local-dev fallback when no RapidAPI key is configured.

    Direct-scrapes youtube.com via ``youtube-transcript-api``. Almost
    certainly fails in production (cloud IP block) — surfacing the
    library's own error message tells the operator what to do.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import (
            NoTranscriptFound,
            TranscriptsDisabled,
            VideoUnavailable,
        )
    except ImportError:
        return NodeResult(
            success=False,
            error=(
                "youtube-transcript-api is not installed in this environment. "
                "Add it to apps/api/pyproject.toml or configure RAPIDAPI_KEY + "
                "RAPIDAPI_YOUTUBE_TRANSCRIPT_HOST to use the cloud-safe path."
            ),
        )

    import asyncio

    def _fetch() -> tuple[list[dict[str, Any]], str]:
        try:
            api = YouTubeTranscriptApi()
            transcript_list = api.list(vid)
            try:
                transcript = transcript_list.find_transcript([preferred])
            except NoTranscriptFound:
                try:
                    transcript = transcript_list.find_generated_transcript([preferred])
                except NoTranscriptFound:
                    transcript = next(iter(transcript_list))
            fetched = transcript.fetch()
            segments = [{"text": s.text, "start": s.start, "duration": s.duration} for s in fetched]
            return segments, transcript.language_code
        except VideoUnavailable as exc:
            raise RuntimeError(f"Video {vid} is unavailable.") from exc
        except TranscriptsDisabled as exc:
            raise RuntimeError(f"Transcripts are disabled for video {vid}.") from exc

    try:
        segments, language = await asyncio.to_thread(_fetch)
    except RuntimeError as exc:
        return NodeResult(success=False, error=str(exc))

    full_text = " ".join(seg["text"] for seg in segments).strip()
    return NodeResult(
        success=True,
        output_data={
            "id": vid,
            "language": language,
            "text": full_text,
            "segments": segments,
            "segment_count": len(segments),
            "source": "direct",
        },
    )


_HANDLERS: dict[str, Any] = {
    "list_my_videos": _list_my_videos,
    "get_video": _get_video,
    "get_video_rating": _get_video_rating,
    "upload_video": _upload_video,
    "update_video": _update_video,
    "delete_video": _delete_video,
    "rate_video": _rate_video,
    "set_video_thumbnail": _set_video_thumbnail,
    "search_videos": _search_videos,
    "list_playlists": _list_playlists,
    "create_playlist": _create_playlist,
    "update_playlist": _update_playlist,
    "delete_playlist": _delete_playlist,
    "add_video_to_playlist": _add_video_to_playlist,
    "remove_video_from_playlist": _remove_video_from_playlist,
    "list_playlist_items": _list_playlist_items,
    "list_comments": _list_comments,
    "post_top_comment": _post_top_comment,
    "reply_to_comment": _reply_to_comment,
    "update_comment": _update_comment,
    "delete_comment": _delete_comment,
    "mark_comment_as_spam": _mark_comment_as_spam,
    "set_comment_moderation_status": _set_comment_moderation_status,
    "get_my_channel": _get_my_channel,
    "get_channel_by_id": _get_channel_by_id,
    "list_subscriptions": _list_subscriptions,
    "subscribe_to_channel": _subscribe_to_channel,
    "unsubscribe_from_channel": _unsubscribe_from_channel,
    "get_public_video": _get_public_video,
    "get_video_transcript": _get_video_transcript,
}
