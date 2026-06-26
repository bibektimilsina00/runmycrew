"""Hacker News action node — manifest form.

HN's official API is hosted on Firebase. No auth. Single host, simple
paths:

  - `/v0/{ranking}.json` for ranked id lists (top / new / best / ask /
    show / job).
  - `/v0/item/{id}.json` for item detail.
  - `/v0/user/{id}.json` for user profile.
  - `/v0/maxitem.json` for the latest item id.

Output isn't enveloped — each endpoint returns either a list of ids
or a single dict, so no flattener needed.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.hackernews",
    name="Hacker News",
    category="integration",
    description="Hacker News Firebase API — top stories, items, users.",
    icon_slug="hackernews",
    color="#1c1c1c",
    base_url="https://hacker-news.firebaseio.com",
    credential_type=None,
    auth="none",
    fields=[
        FieldSpec(name="item_id", label="Item ID", type="number"),
        FieldSpec(name="user_id", label="User ID", type="string"),
    ],
    operations=[
        OpSpec(id="top_stories", label="Top Stories", method="GET", path="/v0/topstories.json"),
        OpSpec(id="new_stories", label="New Stories", method="GET", path="/v0/newstories.json"),
        OpSpec(id="best_stories", label="Best Stories", method="GET", path="/v0/beststories.json"),
        OpSpec(id="ask_stories", label="Ask HN Stories", method="GET", path="/v0/askstories.json"),
        OpSpec(
            id="show_stories", label="Show HN Stories", method="GET", path="/v0/showstories.json"
        ),
        OpSpec(id="job_stories", label="Job Stories", method="GET", path="/v0/jobstories.json"),
        OpSpec(
            id="get_item",
            label="Get Item",
            method="GET",
            path="/v0/item/{item_id}.json",
            visible_fields=["item_id"],
        ),
        OpSpec(
            id="get_user",
            label="Get User",
            method="GET",
            path="/v0/user/{user_id}.json",
            visible_fields=["user_id"],
        ),
        OpSpec(id="max_item", label="Max Item ID", method="GET", path="/v0/maxitem.json"),
    ],
    outputs_schema=[
        {"label": "id", "type": "number"},
        {"label": "type", "type": "string"},
        {"label": "by", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "url", "type": "string"},
        {"label": "score", "type": "number"},
        {"label": "time", "type": "number"},
        {"label": "kids", "type": "array"},
        {"label": "text", "type": "string"},
    ],
    allow_error=True,
)
