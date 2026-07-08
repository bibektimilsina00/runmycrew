"""Jina AI action node — Jina — search, reader, embed via jina.ai.

REST at https://api.jina.ai/v1. See sim-parity roadmap Phase 4.18/4.19.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.jina",
    name="Jina AI",
    category="integration",
    description="Jina — search, reader, embed via jina.ai.",
    icon_slug="jina",
    color="#ffffff",
    base_url="https://api.jina.ai/v1",
    credential_type="jina_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="inbox_id", label="Inbox ID", type="string"),
        FieldSpec(name="message_id", label="Message ID", type="string"),
        FieldSpec(
            name="to", label="To (comma-separated for email; phone number for call)", type="string"
        ),
        FieldSpec(name="from_", label="From", type="string"),
        FieldSpec(name="subject", label="Subject", type="string"),
        FieldSpec(name="text", label="Text / Message Body", type="string"),
        FieldSpec(name="username", label="Username", type="string"),
        FieldSpec(name="domain", label="Domain", type="string"),
        FieldSpec(name="assistant_id", label="Assistant ID", type="string"),
        FieldSpec(name="prompt", label="Prompt", type="string"),
        FieldSpec(name="call_id", label="Call ID", type="string"),
        FieldSpec(name="agent_id", label="Agent ID", type="string"),
        FieldSpec(name="session_id", label="Session ID", type="string"),
        FieldSpec(name="repo", label="Repo (owner/name)", type="string"),
        FieldSpec(name="model", label="Model", type="string"),
        FieldSpec(name="playbook_id", label="Playbook ID", type="string"),
        FieldSpec(name="conversation_id", label="Conversation ID", type="string"),
        FieldSpec(name="messages", label="Messages (JSON array)", type="json"),
        FieldSpec(name="metadata", label="Metadata (JSON)", type="json"),
        FieldSpec(name="start_date", label="Start Date", type="string"),
        FieldSpec(name="end_date", label="End Date", type="string"),
        FieldSpec(name="url", label="URL", type="string"),
        FieldSpec(name="file_id", label="File ID", type="string"),
        FieldSpec(name="query", label="Query", type="string"),
        FieldSpec(name="input", label="Input(s) (pipe-separated)", type="string"),
        FieldSpec(name="documents", label="Documents (JSON array)", type="json"),
        FieldSpec(name="config", label="Config (JSON)", type="json"),
        FieldSpec(name="job_id", label="Job ID", type="string"),
        FieldSpec(name="project_id", label="Project ID", type="string"),
        FieldSpec(name="dataset_id", label="Dataset ID", type="string"),
        FieldSpec(name="snapshot_id", label="Snapshot ID", type="string"),
        FieldSpec(name="program_id", label="Program ID", type="string"),
        FieldSpec(name="inputs", label="Inputs (JSON)", type="json"),
        FieldSpec(name="limit", label="Limit", type="number", default=25, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="reader",
            label="Reader (URL → Markdown)",
            method="POST",
            path="/reader",
            visible_fields=["url"],
            body_builder=lambda v: {"url": getattr(v, "url", "") or ""},
        ),
        OpSpec(
            id="search",
            label="Web Search",
            method="POST",
            path="/search",
            visible_fields=["query"],
            body_builder=lambda v: {"q": getattr(v, "query", "") or ""},
        ),
        OpSpec(
            id="embed",
            label="Embeddings",
            method="POST",
            path="/embeddings",
            visible_fields=["input", "model"],
            body_builder=lambda v: {
                "input": [
                    t.strip() for t in (getattr(v, "input", "") or "").split("|") if t.strip()
                ],
                "model": getattr(v, "model", None) or "jina-embeddings-v3",
            },
        ),
        OpSpec(
            id="rerank",
            label="Rerank",
            method="POST",
            path="/rerank",
            visible_fields=["query", "documents", "model"],
            body_builder=lambda v: {
                "query": getattr(v, "query", "") or "",
                "documents": getattr(v, "documents", None) or [],
                "model": getattr(v, "model", None) or "jina-reranker-v2-base-multilingual",
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
