"""DuckDuckGo Instant Answer node — manifest form.

DuckDuckGo's Instant Answer API serves quick zero-click answers
(definitions, calculator, conversions, Wikipedia summaries). No auth,
no per-request limits beyond rate-limiting on abuse.

This is the *Instant Answer* API — not a general web search. For full
SERP results use Exa, Serper, or Tavily.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.duckduckgo",
    name="DuckDuckGo",
    category="integration",
    description="DuckDuckGo Instant Answer API — definitions, calculator, quick facts.",
    icon_slug="duckduckgo",
    color="#1c1c1c",
    base_url="https://api.duckduckgo.com",
    credential_type=None,
    auth="none",
    fields=[
        FieldSpec(
            name="q", label="Query", type="string", required=True, placeholder="python language"
        ),
        FieldSpec(
            name="no_html",
            label="Strip HTML",
            type="boolean",
            default=True,
            mode="advanced",
        ),
        FieldSpec(
            name="skip_disambig",
            label="Skip Disambiguation",
            type="boolean",
            default=True,
            mode="advanced",
        ),
    ],
    operations=[
        OpSpec(
            id="instant_answer",
            label="Instant Answer",
            method="GET",
            path="/",
            visible_fields=["q", "no_html", "skip_disambig"],
            query_builder=lambda props: {
                "q": getattr(props, "q", None) or "",
                "format": "json",
                "no_html": "1" if getattr(props, "no_html", True) else "0",
                "skip_disambig": "1" if getattr(props, "skip_disambig", True) else "0",
            },
        ),
    ],
    outputs_schema=[
        {"label": "Abstract", "type": "string"},
        {"label": "AbstractText", "type": "string"},
        {"label": "AbstractSource", "type": "string"},
        {"label": "AbstractURL", "type": "string"},
        {"label": "Answer", "type": "string"},
        {"label": "AnswerType", "type": "string"},
        {"label": "Definition", "type": "string"},
        {"label": "DefinitionSource", "type": "string"},
        {"label": "Heading", "type": "string"},
        {"label": "RelatedTopics", "type": "array"},
    ],
    allow_error=True,
)
