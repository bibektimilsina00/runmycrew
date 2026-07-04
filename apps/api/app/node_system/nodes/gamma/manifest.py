"""Gamma action node — Gamma — AI-generated presentations, docs, sites.

REST at https://public-api.gamma.app/v0.2. See sim-parity roadmap Phase 4.29.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.gamma",
    name="Gamma",
    category="integration",
    description="Gamma — AI-generated presentations, docs, sites.",
    icon_slug="gamma",
    color="#1c1c1c",
    base_url="https://public-api.gamma.app/v0.2",
    credential_type="gamma_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="X-API-KEY",
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
            id="create_generation",
            label="Create Generation",
            method="POST",
            path="/generations",
            visible_fields=["input_text", "format", "num_cards", "text_amount"],
            body_builder=lambda v: {
                "inputText": getattr(v, "input_text", "") or "",
                "format": getattr(v, "format", None) or "presentation",
                "numCards": int(getattr(v, "num_cards", 10) or 10),
                "textAmount": getattr(v, "text_amount", None) or "detailed",
            },
        ),
        OpSpec(
            id="get_generation",
            label="Get Generation Status",
            method="GET",
            path="/generations/{generation_id}",
            visible_fields=["generation_id"],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
