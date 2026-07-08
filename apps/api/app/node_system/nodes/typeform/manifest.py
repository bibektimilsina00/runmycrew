"""Typeform action node — manifest form.

Typeform REST API at `https://api.typeform.com`. Bearer auth using a
personal access token. Six ops cover the workflow basics: list forms,
get form, list/get responses, create webhook.
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.typeform import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)

MANIFEST = ProviderManifest(
    type="action.typeform",
    name=NAME,
    category="integration",
    description="Typeform — list forms, fetch responses, manage webhooks.",
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://api.typeform.com",
    credential_type="typeform_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(
            name="form_id",
            label="Form",
            type="string",
            remote=RemoteLookup(provider="typeform", resource="forms"),
        ),
        FieldSpec(name="tag", label="Webhook Tag", type="string", placeholder="my-webhook"),
        FieldSpec(name="webhook_url", label="Webhook URL", type="string"),
        FieldSpec(name="enabled", label="Enabled", type="boolean", default=True, mode="advanced"),
        FieldSpec(name="since", label="Since (ISO 8601)", type="string", mode="advanced"),
        FieldSpec(name="until", label="Until (ISO 8601)", type="string", mode="advanced"),
        FieldSpec(name="completed", label="Only completed", type="boolean", mode="advanced"),
        FieldSpec(name="page_size", label="Page size", type="number", default=25, mode="advanced"),
        FieldSpec(name="response_id", label="Response ID", type="string"),
    ],
    operations=[
        OpSpec(id="list_forms", label="List Forms", method="GET", path="/forms"),
        OpSpec(
            id="get_form",
            label="Get Form",
            method="GET",
            path="/forms/{form_id}",
            visible_fields=["form_id"],
        ),
        OpSpec(
            id="list_responses",
            label="List Responses",
            method="GET",
            path="/forms/{form_id}/responses",
            visible_fields=["form_id", "since", "until", "completed", "page_size"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "since": getattr(v, "since", None),
                    "until": getattr(v, "until", None),
                    "completed": (
                        "true"
                        if getattr(v, "completed", None) is True
                        else ("false" if getattr(v, "completed", None) is False else None)
                    ),
                    "page_size": int(getattr(v, "page_size", 25) or 25),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_response",
            label="Get Response",
            method="GET",
            path="/forms/{form_id}/responses",
            visible_fields=["form_id", "response_id"],
            query_builder=lambda v: {
                "included_response_ids": getattr(v, "response_id", None) or "",
            },
        ),
        OpSpec(
            id="create_webhook",
            label="Create Webhook",
            method="PUT",
            path="/forms/{form_id}/webhooks/{tag}",
            visible_fields=["form_id", "tag", "webhook_url", "enabled"],
            body_builder=lambda v: {
                "url": getattr(v, "webhook_url", None),
                "enabled": bool(getattr(v, "enabled", True)),
            },
        ),
        OpSpec(
            id="list_webhooks",
            label="List Webhooks",
            method="GET",
            path="/forms/{form_id}/webhooks",
            visible_fields=["form_id"],
        ),
        OpSpec(
            id="delete_webhook",
            label="Delete Webhook",
            method="DELETE",
            path="/forms/{form_id}/webhooks/{tag}",
            visible_fields=["form_id", "tag"],
            success_payload_template={"deleted": True, "tag": "{tag}"},
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "items", "type": "array"},
        {"label": "total_items", "type": "number"},
        {"label": "page_count", "type": "number"},
        {"label": "url", "type": "string"},
    ],
    allow_error=True,
)
