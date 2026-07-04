"""PostHog action node — manifest form.

PostHog has two API surfaces:

  - **Capture API** at `https://us.i.posthog.com` for event ingestion.
    Uses `api_key` *in the body* (project key, not personal). The
    user-facing prop is `api_key` but it lives at the project level,
    not the credential token. We pass the credential's personal token
    via Bearer for queries; capture ops use the project key from the
    request body.
  - **Personal/Project API** at `https://us.posthog.com/api/projects/{project_id}/`
    for everything else — feature flags, queries, persons, cohorts.
    Bearer auth with a personal API key.

This manifest covers the API surface (queries, flags, persons). Event
capture lives in a separate `posthog-capture` integration if we need it
later — different auth model, different base URL.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.posthog",
    name="PostHog",
    category="integration",
    description="Query PostHog events, manage feature flags + persons.",
    icon_slug="posthog",
    color="#1c1c1c",
    base_url="https://us.posthog.com/api",
    credential_type="posthog_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(
            name="project_id", label="Project ID", type="string", required=True, placeholder="12345"
        ),
        FieldSpec(name="flag_id", label="Feature Flag ID", type="string"),
        FieldSpec(name="flag_key", label="Feature Flag Key", type="string"),
        FieldSpec(name="active", label="Active", type="boolean", mode="advanced"),
        FieldSpec(name="filters", label="Filters (JSON)", type="json", mode="advanced"),
        FieldSpec(name="person_id", label="Person ID", type="string"),
        FieldSpec(name="distinct_id", label="Distinct ID", type="string"),
        FieldSpec(
            name="query",
            label="HogQL Query",
            type="string",
            placeholder="SELECT count() FROM events",
        ),
        FieldSpec(name="limit", label="Limit", type="number", default=100, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="run_query",
            label="Run HogQL Query",
            method="POST",
            path="/projects/{project_id}/query/",
            visible_fields=["project_id", "query"],
            body_template={"query": {"kind": "HogQLQuery", "query": "{query}"}},
        ),
        OpSpec(
            id="list_feature_flags",
            label="List Feature Flags",
            method="GET",
            path="/projects/{project_id}/feature_flags/",
            visible_fields=["project_id", "limit"],
            query_fields=["limit"],
        ),
        OpSpec(
            id="get_feature_flag",
            label="Get Feature Flag",
            method="GET",
            path="/projects/{project_id}/feature_flags/{flag_id}/",
            visible_fields=["project_id", "flag_id"],
        ),
        OpSpec(
            id="create_feature_flag",
            label="Create Feature Flag",
            method="POST",
            path="/projects/{project_id}/feature_flags/",
            visible_fields=["project_id", "flag_key", "active", "filters"],
            body_builder=lambda props: {
                k: v
                for k, v in {
                    "key": getattr(props, "flag_key", None),
                    "name": getattr(props, "flag_key", None),
                    "active": getattr(props, "active", None),
                    "filters": getattr(props, "filters", None),
                }.items()
                if v is not None
            },
        ),
        OpSpec(
            id="update_feature_flag",
            label="Update Feature Flag",
            method="PATCH",
            path="/projects/{project_id}/feature_flags/{flag_id}/",
            visible_fields=["project_id", "flag_id", "active", "filters"],
            body_builder=lambda props: {
                k: v
                for k, v in {
                    "active": getattr(props, "active", None),
                    "filters": getattr(props, "filters", None),
                }.items()
                if v is not None
            },
        ),
        OpSpec(
            id="list_persons",
            label="List Persons",
            method="GET",
            path="/projects/{project_id}/persons/",
            visible_fields=["project_id", "distinct_id", "limit"],
            query_fields=["distinct_id", "limit"],
        ),
        OpSpec(
            id="get_person",
            label="Get Person",
            method="GET",
            path="/projects/{project_id}/persons/{person_id}/",
            visible_fields=["project_id", "person_id"],
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "key", "type": "string"},
        {"label": "active", "type": "boolean"},
        {"label": "results", "type": "array"},
        {"label": "count", "type": "number"},
        {"label": "next", "type": "string"},
    ],
    allow_error=True,
)
