"""Reddit action node — Reddit — subreddit browsing, submissions, comments.

REST at https://oauth.reddit.com. See sim-parity roadmap Phase 4.29.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.reddit",
    name="Reddit",
    category="integration",
    description="Reddit — subreddit browsing, submissions, comments.",
    icon_slug="reddit",
    color="#FF4500",
    base_url="https://oauth.reddit.com",
    credential_type="reddit_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="query", label="Query", type="string"),
        FieldSpec(
            name="max_results", label="Max Results", type="number", default=10, mode="advanced"
        ),
        FieldSpec(name="type", label="Type", type="string"),
        FieldSpec(name="video_id", label="Video ID", type="string"),
        FieldSpec(name="channel_id", label="Channel ID", type="string"),
        FieldSpec(name="playlist_id", label="Playlist ID", type="string"),
        FieldSpec(name="post_id", label="Post ID", type="string"),
        FieldSpec(name="title", label="Title", type="string"),
        FieldSpec(name="content", label="Content (HTML)", type="string"),
        FieldSpec(name="status", label="Status", type="string", default="draft"),
        FieldSpec(name="per_page", label="Per Page", type="number", default=10, mode="advanced"),
        FieldSpec(name="text", label="Text", type="string"),
        FieldSpec(name="tweet_id", label="Tweet ID", type="string"),
        FieldSpec(name="username", label="Username", type="string"),
        FieldSpec(name="subreddit", label="Subreddit", type="string"),
        FieldSpec(name="sort", label="Sort", type="string", default="hot"),
        FieldSpec(name="limit", label="Limit", type="number", default=10, mode="advanced"),
        FieldSpec(name="url", label="URL", type="string"),
        FieldSpec(name="kind", label="Kind (self|link)", type="string", default="self"),
        FieldSpec(name="article", label="Article ID", type="string"),
        FieldSpec(name="track_id", label="Track ID", type="string"),
        FieldSpec(name="artist_id", label="Artist ID", type="string"),
        FieldSpec(name="user_id", label="User ID", type="string"),
        FieldSpec(name="playlist_name", label="Playlist Name", type="string"),
        FieldSpec(name="playlist_description", label="Playlist Description", type="string"),
        FieldSpec(name="public", label="Public Playlist", type="boolean", default=False),
        FieldSpec(name="track_uris", label="Track URIs (JSON)", type="json", default=[]),
        FieldSpec(name="prompt_image", label="Prompt Image URL", type="string"),
        FieldSpec(name="prompt_text", label="Prompt Text", type="string"),
        FieldSpec(name="duration", label="Duration (sec)", type="number", default=5),
        FieldSpec(name="ratio", label="Aspect Ratio", type="string", default="1280:768"),
        FieldSpec(name="task_id", label="Task ID", type="string"),
        FieldSpec(name="input_text", label="Input Text", type="string"),
        FieldSpec(name="format", label="Format", type="string", default="presentation"),
        FieldSpec(name="num_cards", label="Number of Cards", type="number", default=10),
        FieldSpec(name="text_amount", label="Text Amount", type="string", default="detailed"),
        FieldSpec(name="generation_id", label="Generation ID", type="string"),
    ],
    operations=[
        OpSpec(
            id="list_subreddit",
            label="List Subreddit Posts",
            method="GET",
            path="/r/{subreddit}/{sort}",
            visible_fields=["subreddit", "sort", "limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 10) or 10)},
        ),
        OpSpec(
            id="submit",
            label="Submit Post",
            method="POST",
            path="/api/submit",
            visible_fields=["subreddit", "title", "url", "text", "kind"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "sr": getattr(v, "subreddit", "") or "",
                    "title": getattr(v, "title", "") or "",
                    "url": getattr(v, "url", None) or None,
                    "text": getattr(v, "text", None) or None,
                    "kind": getattr(v, "kind", None) or "self",
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_comments",
            label="Get Post Comments",
            method="GET",
            path="/comments/{article}",
            visible_fields=["article"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="search",
            label="Search Reddit",
            method="GET",
            path="/search",
            visible_fields=["query", "limit"],
            query_builder=lambda v: {
                "q": getattr(v, "query", "") or "",
                "limit": int(getattr(v, "limit", 10) or 10),
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
