"""Fireflies action node — manifest form.

Fireflies.ai serves a GraphQL API at `https://api.fireflies.ai/graphql`.
Every op is a `CustomHandler` — scaffold owns credential injection +
inspector schema; handlers own the GraphQL body.

Auth uses `Authorization: Bearer <key>` — standard bearer scheme.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.fireflies import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

FIREFLIES_API = "https://api.fireflies.ai/graphql"


async def _gql(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    query: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resp = await client.post(
        FIREFLIES_API,
        headers={**headers, "Content-Type": "application/json"},
        json={"query": query, "variables": variables or {}},
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json() or {}
    if body.get("errors"):
        raise RuntimeError(body["errors"][0].get("message") or "Fireflies GraphQL error")
    return body.get("data") or {}


async def _list_transcripts(
    node: Any, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    limit = int(getattr(node.props, "limit", 10) or 10)
    query = (
        "query ListTranscripts($limit: Int) {"
        " transcripts(limit: $limit) {"
        " id title date duration meeting_url"
        " participants organizer_email"
        " summary { keywords action_items overview }"
        " }"
        " }"
    )
    data = await _gql(client, headers, query, {"limit": limit})
    transcripts = data.get("transcripts") or []
    return NodeResult(
        success=True, output_data={"transcripts": transcripts, "count": len(transcripts)}
    )


async def _get_transcript(
    node: Any, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    transcript_id = getattr(node.props, "transcript_id", None)
    if not transcript_id:
        return NodeResult(success=False, error="transcript_id required")
    query = (
        "query GetTranscript($id: String!) {"
        " transcript(id: $id) {"
        " id title date duration meeting_url participants organizer_email"
        " summary { keywords action_items overview }"
        " sentences { text speaker_name start_time }"
        " }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": str(transcript_id)})
    return NodeResult(success=True, output_data=data.get("transcript") or {})


async def _search_transcripts(
    node: Any, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    keyword = getattr(node.props, "query", None) or ""
    limit = int(getattr(node.props, "limit", 10) or 10)
    query = (
        "query Search($keyword: String!, $limit: Int) {"
        " transcripts(keyword: $keyword, limit: $limit) {"
        " id title date meeting_url summary { overview }"
        " }"
        " }"
    )
    data = await _gql(client, headers, query, {"keyword": keyword, "limit": limit})
    transcripts = data.get("transcripts") or []
    return NodeResult(
        success=True, output_data={"transcripts": transcripts, "count": len(transcripts)}
    )


async def _get_user(node: Any, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
    query = "query { user { user_id name email num_transcripts } }"
    data = await _gql(client, headers, query)
    return NodeResult(success=True, output_data=data.get("user") or {})


async def _list_users(node: Any, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
    query = "query { users { user_id name email num_transcripts } }"
    data = await _gql(client, headers, query)
    users = data.get("users") or []
    return NodeResult(success=True, output_data={"users": users, "count": len(users)})


MANIFEST = ProviderManifest(
    type="action.fireflies",
    name=NAME,
    category="integration",
    description="Fireflies.ai — meeting transcripts, summaries, search via GraphQL.",
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://api.fireflies.ai",
    credential_type="fireflies_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="transcript_id", label="Transcript ID", type="string"),
        FieldSpec(name="query", label="Search Keyword", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=10, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_transcripts",
            label="List Transcripts",
            visible_fields=["limit"],
            handler=_list_transcripts,
        ),
        OpSpec(
            id="get_transcript",
            label="Get Transcript",
            visible_fields=["transcript_id"],
            handler=_get_transcript,
        ),
        OpSpec(
            id="search_transcripts",
            label="Search Transcripts",
            visible_fields=["query", "limit"],
            handler=_search_transcripts,
        ),
        OpSpec(id="get_user", label="Get Current User", handler=_get_user),
        OpSpec(id="list_users", label="List Users", handler=_list_users),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "summary", "type": "object"},
        {"label": "sentences", "type": "array"},
        {"label": "transcripts", "type": "array"},
        {"label": "users", "type": "array"},
    ],
    allow_error=True,
)
