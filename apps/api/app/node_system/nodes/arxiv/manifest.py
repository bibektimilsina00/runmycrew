"""arXiv action node — arXiv — search preprints (returns Atom XML in body).

REST at http://export.arxiv.org/api. See sim-parity roadmap Phase 4.31.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.arxiv",
    name="arXiv",
    category="integration",
    description="arXiv — search preprints (returns Atom XML in body).",
    icon_slug="arxiv",
    color="#B31B1B",
    base_url="http://export.arxiv.org/api",
    credential_type=None,
    token_field=["api_key"],
    auth="none",
    fields=[
        FieldSpec(name="phone_number_id", label="Phone Number ID", type="string"),
        FieldSpec(name="to", label="To", type="string"),
        FieldSpec(name="text_body", label="Text Body", type="string"),
        FieldSpec(name="template_name", label="Template Name", type="string"),
        FieldSpec(name="language_code", label="Language Code", type="string", default="en_US"),
        FieldSpec(
            name="media_type",
            label="Media Type (image|video|document|audio)",
            type="string",
            default="image",
        ),
        FieldSpec(name="media_link", label="Media URL", type="string"),
        FieldSpec(name="caption", label="Caption", type="string"),
        FieldSpec(name="from_number", label="From (E.164)", type="string"),
        FieldSpec(name="url", label="TwiML URL", type="string"),
        FieldSpec(name="call_sid", label="Call SID", type="string"),
        FieldSpec(name="status", label="Status", type="string"),
        FieldSpec(name="query", label="Query", type="string"),
        FieldSpec(
            name="max_results", label="Max Results", type="number", default=10, mode="advanced"
        ),
        FieldSpec(name="sort_by", label="Sort By", type="string", default="relevance"),
        FieldSpec(name="sort_order", label="Sort Order", type="string", default="descending"),
        FieldSpec(name="arxiv_ids", label="arXiv IDs (JSON array)", type="json", default=[]),
    ],
    operations=[
        OpSpec(
            id="search",
            label="Search arXiv",
            method="GET",
            path="/query",
            visible_fields=["query", "max_results", "sort_by", "sort_order"],
            query_builder=lambda v: {
                "search_query": getattr(v, "query", "") or "",
                "max_results": int(getattr(v, "max_results", 10) or 10),
                "sortBy": getattr(v, "sort_by", None) or "relevance",
                "sortOrder": getattr(v, "sort_order", None) or "descending",
            },
        ),
        OpSpec(
            id="get_by_id",
            label="Get by arXiv ID(s)",
            method="GET",
            path="/query",
            visible_fields=["arxiv_ids"],
            query_builder=lambda v: {"id_list": ",".join(getattr(v, "arxiv_ids", []) or [])},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
