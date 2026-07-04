"""AgentMail action node — AgentMail — AI email agent (send, receive, thread).

REST at https://api.agentmail.to/v0. See sim-parity roadmap Phase 4.18/4.19.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.agentmail",
    name="AgentMail",
    category="integration",
    description="AgentMail — AI email agent (send, receive, thread).",
    icon_slug="agentmail",
    color="#1c1c1c",
    base_url="https://api.agentmail.to/v0",
    credential_type="agentmail_api_key",
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
            id="send_message",
            label="Send Message",
            method="POST",
            path="/inboxes/{inbox_id}/messages/send",
            visible_fields=["inbox_id", "to", "subject", "text"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "to": [t.strip() for t in (getattr(v, "to", "") or "").split(",") if t.strip()],
                    "subject": getattr(v, "subject", None) or None,
                    "text": getattr(v, "text", None) or None,
                }.items()
                if val
            },
        ),
        OpSpec(
            id="list_messages",
            label="List Messages",
            method="GET",
            path="/inboxes/{inbox_id}/messages",
            visible_fields=["inbox_id", "limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 25) or 25)},
        ),
        OpSpec(
            id="get_message",
            label="Get Message",
            method="GET",
            path="/inboxes/{inbox_id}/messages/{message_id}",
            visible_fields=["inbox_id", "message_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_inboxes",
            label="List Inboxes",
            method="GET",
            path="/inboxes",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_inbox",
            label="Create Inbox",
            method="POST",
            path="/inboxes",
            visible_fields=["username", "domain"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "username": getattr(v, "username", None) or None,
                    "domain": getattr(v, "domain", None) or None,
                }.items()
                if val
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
