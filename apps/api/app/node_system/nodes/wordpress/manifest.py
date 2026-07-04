"""WordPress action node — WordPress — posts, pages, media (REST API).

REST at https://{site}/wp-json/wp/v2. See sim-parity roadmap Phase 4.29.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.wordpress",
    name="WordPress",
    category="integration",
    description="WordPress — posts, pages, media (REST API).",
    icon_slug="wordpress",
    color="#21759B",
    base_url="https://{site}/wp-json/wp/v2",
    credential_type="wordpress_api_key",
    token_field=["api_key"],
    auth="basic",
    auth_basic_username="{username}",
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
            id="list_posts",
            label="List Posts",
            method="GET",
            path="/posts",
            visible_fields=["per_page", "status"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "per_page": int(getattr(v, "per_page", 10) or 10),
                    "status": getattr(v, "status", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_post",
            label="Get Post",
            method="GET",
            path="/posts/{post_id}",
            visible_fields=["post_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_post",
            label="Create Post",
            method="POST",
            path="/posts",
            visible_fields=["title", "content", "status"],
            body_builder=lambda v: {
                "title": getattr(v, "title", "") or "",
                "content": getattr(v, "content", "") or "",
                "status": getattr(v, "status", None) or "draft",
            },
        ),
        OpSpec(
            id="update_post",
            label="Update Post",
            method="POST",
            path="/posts/{post_id}",
            visible_fields=["post_id", "title", "content", "status"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "title": getattr(v, "title", None) or None,
                    "content": getattr(v, "content", None) or None,
                    "status": getattr(v, "status", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="delete_post",
            label="Delete Post",
            method="DELETE",
            path="/posts/{post_id}",
            visible_fields=["post_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_pages",
            label="List Pages",
            method="GET",
            path="/pages",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
