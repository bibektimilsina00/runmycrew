"""LaTeX (latexonline.cc) action node — LaTeX Online — compile .tex to PDF via a public renderer.

REST at https://latexonline.cc. See sim-parity roadmap Phase 4.32.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.latex",
    name="LaTeX (latexonline.cc)",
    category="integration",
    description="LaTeX Online — compile .tex to PDF via a public renderer.",
    icon_slug="latex",
    color="#008080",
    base_url="https://latexonline.cc",
    credential_type=None,
    token_field=["api_key"],
    auth="none",
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
        FieldSpec(name="schema", label="Schema (JSON)", type="json", default={}),
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
            id="compile_from_source",
            label="Compile from LaTeX Source",
            method="POST",
            path="/data",
            visible_fields=["source"],
            body_builder=lambda v: getattr(v, "source", "") or "",
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
