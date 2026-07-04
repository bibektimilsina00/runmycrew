"""Cursor action node — Cursor — AI code editor. Background agents API.

REST at https://api.cursor.com. See sim-parity roadmap Phase 4.18/4.19.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.cursor",
    name="Cursor",
    category="integration",
    description="Cursor — AI code editor. Background agents API.",
    icon_slug="cursor",
    color="#1c1c1c",
    base_url="https://api.cursor.com",
    credential_type="cursor_api_key",
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
            id="create_agent",
            label="Create Background Agent",
            method="POST",
            path="/agents",
            visible_fields=["repo", "prompt", "model"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "repo": getattr(v, "repo", None) or None,
                    "prompt": getattr(v, "prompt", None) or None,
                    "model": getattr(v, "model", None) or None,
                }.items()
                if val
            },
        ),
        OpSpec(
            id="get_agent",
            label="Get Agent Status",
            method="GET",
            path="/agents/{agent_id}",
            visible_fields=["agent_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_agents",
            label="List Agents",
            method="GET",
            path="/agents",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 25) or 25)},
        ),
        OpSpec(
            id="cancel_agent",
            label="Cancel Agent",
            method="POST",
            path="/agents/{agent_id}/cancel",
            visible_fields=["agent_id"],
            body_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
