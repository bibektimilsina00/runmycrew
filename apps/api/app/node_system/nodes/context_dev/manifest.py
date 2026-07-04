"""Context action node — Context — LLM answer analytics + user feedback.

REST at https://api.getcontext.dev/v1. See sim-parity roadmap Phase 4.18/4.19.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.context_dev",
    name="Context",
    category="integration",
    description="Context — LLM answer analytics + user feedback.",
    icon_slug="context_dev",
    color="#1c1c1c",
    base_url="https://api.getcontext.dev/v1",
    credential_type="context_dev_api_key",
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
            id="log_conversation",
            label="Log Conversation",
            method="POST",
            path="/pipelines/log",
            visible_fields=["conversation_id", "messages", "metadata"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "conversation_id": getattr(v, "conversation_id", None) or None,
                    "messages": getattr(v, "messages", None) or None,
                    "metadata": getattr(v, "metadata", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_analytics",
            label="Get Analytics",
            method="GET",
            path="/analytics/topics",
            visible_fields=["start_date", "end_date"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "start_date": getattr(v, "start_date", None) or None,
                    "end_date": getattr(v, "end_date", None) or None,
                }.items()
                if val is not None
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
