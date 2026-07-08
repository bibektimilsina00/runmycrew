"""Stagehand action node — Stagehand — Browserbase AI browser automation.

REST at https://api.browserbase.com/v1. See sim-parity roadmap Phase 4.18/4.19.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.stagehand",
    name="Stagehand",
    category="integration",
    description="Stagehand — Browserbase AI browser automation.",
    icon_slug="stagehand",
    color="#ffffff",
    base_url="https://api.browserbase.com/v1",
    credential_type="stagehand_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="X-BB-API-Key",
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
            id="create_session",
            label="Create Session",
            method="POST",
            path="/sessions",
            visible_fields=["project_id"],
            body_builder=lambda v: {"projectId": getattr(v, "project_id", "") or ""},
        ),
        OpSpec(
            id="get_session",
            label="Get Session",
            method="GET",
            path="/sessions/{session_id}",
            visible_fields=["session_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_sessions",
            label="List Sessions",
            method="GET",
            path="/sessions",
            visible_fields=["project_id"],
            query_builder=lambda v: {
                k: val
                for k, val in {"projectId": getattr(v, "project_id", None) or None}.items()
                if val
            },
        ),
        OpSpec(
            id="get_recording",
            label="Get Session Recording",
            method="GET",
            path="/sessions/{session_id}/recording",
            visible_fields=["session_id"],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
