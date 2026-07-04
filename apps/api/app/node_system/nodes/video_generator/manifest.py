"""Video Generator (Runway/HeyGen) action node — Runway Gen-3 video generation — text/image → video.

REST at https://api.dev.runwayml.com/v1. See sim-parity roadmap Phase 4.29.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.video_generator",
    name="Video Generator (Runway/HeyGen)",
    category="integration",
    description="Runway Gen-3 video generation — text/image → video.",
    icon_slug="video_generator",
    color="#1c1c1c",
    base_url="https://api.dev.runwayml.com/v1",
    credential_type="video_generator_api_key",
    token_field=["api_key"],
    auth="bearer",
    extra_headers={"X-Runway-Version": "2024-11-06"},
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
            id="generate_from_image",
            label="Generate Video from Image",
            method="POST",
            path="/image_to_video",
            visible_fields=["prompt_image", "prompt_text", "duration", "ratio"],
            body_builder=lambda v: {
                "promptImage": getattr(v, "prompt_image", "") or "",
                "promptText": getattr(v, "prompt_text", None) or None,
                "model": "gen3a_turbo",
                "duration": int(getattr(v, "duration", 5) or 5),
                "ratio": getattr(v, "ratio", None) or "1280:768",
            },
        ),
        OpSpec(
            id="get_task",
            label="Get Task Status",
            method="GET",
            path="/tasks/{task_id}",
            visible_fields=["task_id"],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
