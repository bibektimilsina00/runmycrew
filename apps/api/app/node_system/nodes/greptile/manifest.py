"""Greptile action node — Greptile — natural-language code search over your repos.

REST at https://api.greptile.com/v2. See sim-parity roadmap Phase 4.32.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.greptile",
    name="Greptile",
    category="integration",
    description="Greptile — natural-language code search over your repos.",
    icon_slug="greptile",
    color="#ffffff",
    base_url="https://api.greptile.com/v2",
    credential_type="greptile_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="table", label="Table", type="string"),
        FieldSpec(name="record_id", label="Record ID", type="string"),
        FieldSpec(name="filter", label="Filter", type="string"),
        FieldSpec(name="data", label="Data (JSON)", type="json", default={}),
        FieldSpec(name="config_id", label="Sync Config ID", type="string"),
        FieldSpec(name="query_text", label="Query Text", type="string"),
        FieldSpec(name="destination_id", label="Destination ID", type="string"),
        FieldSpec(name="property_id", label="Property ID", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="right", label="Right (delete|access|...)", type="string", default="delete"),
        FieldSpec(name="source", label="LaTeX Source", type="string"),
        FieldSpec(name="query", label="Query", type="string"),
        FieldSpec(name="depth", label="Depth (standard|deep)", type="string", default="standard"),
        FieldSpec(name="output_type", label="Output Type", type="string", default="searchResults"),
        FieldSpec(name="supplier_id", label="Supplier ID", type="string"),
        FieldSpec(name="path", label="Path", type="string"),
        FieldSpec(name="content", label="Content", type="string"),
        FieldSpec(name="message", label="Message", type="string"),
        FieldSpec(name="project_id", label="Project ID", type="string"),
        FieldSpec(name="file_url", label="File URL", type="string"),
        FieldSpec(name="json_schema", label="Schema (JSON)", type="json", default={}),
        FieldSpec(name="job_id", label="Job ID", type="string"),
        FieldSpec(name="company_id", label="Company ID", type="string"),
        FieldSpec(name="event_id", label="Event ID", type="string"),
        FieldSpec(name="remote", label="Remote (github|gitlab)", type="string", default="github"),
        FieldSpec(name="repository", label="Repository (owner/repo)", type="string"),
        FieldSpec(name="branch", label="Branch", type="string", default="main"),
        FieldSpec(name="repositories", label="Repositories (JSON)", type="json", default=[]),
        FieldSpec(name="guard_name", label="Guard Name", type="string"),
        FieldSpec(name="llm_output", label="LLM Output", type="string"),
        FieldSpec(name="host_ids", label="Host IDs (JSON)", type="json", default=[]),
        FieldSpec(name="limit", label="Limit", type="number", default=50, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="submit_repo",
            label="Submit Repo for Indexing",
            method="POST",
            path="/repositories",
            visible_fields=["remote", "repository", "branch"],
            body_builder=lambda v: {
                "remote": getattr(v, "remote", None) or "github",
                "repository": getattr(v, "repository", "") or "",
                "branch": getattr(v, "branch", None) or "main",
            },
        ),
        OpSpec(
            id="query",
            label="Query Code",
            method="POST",
            path="/query",
            visible_fields=["query", "repositories"],
            body_builder=lambda v: {
                "messages": [{"content": getattr(v, "query", "") or "", "role": "user"}],
                "repositories": getattr(v, "repositories", []) or [],
            },
        ),
        OpSpec(
            id="search",
            label="Search Code",
            method="POST",
            path="/search",
            visible_fields=["query", "repositories"],
            body_builder=lambda v: {
                "query": getattr(v, "query", "") or "",
                "repositories": getattr(v, "repositories", []) or [],
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
