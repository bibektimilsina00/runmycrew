"""DocuSign action node — manifest form.

DocuSign's REST API is per-account: the base URL comes back from the
OAuth `userinfo` call as `{base_uri}/restapi/v2.1/accounts/{account_id}`.

The credential carries `base_url` (e.g. `https://na1.docusign.net/restapi/v2.1`)
and `account_id`. We template both into path — same trick as Supabase.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)

_ACCOUNT = "{base_url}/accounts/{account_id}"

MANIFEST = ProviderManifest(
    type="action.docusign",
    name="DocuSign",
    category="integration",
    description="DocuSign — send envelopes, manage templates, track signatures.",
    icon_slug="docusign",
    color="#ffffff",
    base_url="",
    credential_type=["docusign_oauth", "docusign_creds"],
    token_field=["access_token", "api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="envelope_id", label="Envelope ID", type="string"),
        FieldSpec(
            name="template_id",
            label="Template",
            type="string",
            remote=RemoteLookup(provider="docusign", resource="templates"),
        ),
        FieldSpec(name="email_subject", label="Email Subject", type="string"),
        FieldSpec(name="email_body", label="Email Body", type="string", mode="advanced"),
        FieldSpec(
            name="status",
            label="Envelope Status",
            type="options",
            default="sent",
            mode="advanced",
            options=[
                {"label": "Draft (created)", "value": "created"},
                {"label": "Send now", "value": "sent"},
            ],
        ),
        FieldSpec(
            name="documents",
            label="Documents (JSON array)",
            type="json",
            description=(
                "Each: {name, fileExtension, documentId, documentBase64}. "
                "Provide either documents + recipients or template_id + template_roles."
            ),
        ),
        FieldSpec(name="recipients", label="Recipients (JSON)", type="json"),
        FieldSpec(name="template_roles", label="Template Roles (JSON array)", type="json"),
        FieldSpec(name="from_date", label="From Date (ISO)", type="string", mode="advanced"),
        FieldSpec(name="count", label="Page size", type="number", default=25, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_envelopes",
            label="List Envelopes",
            method="GET",
            path=_ACCOUNT + "/envelopes",
            visible_fields=["from_date", "count"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "from_date": getattr(v, "from_date", None),
                    "count": int(getattr(v, "count", 25) or 25),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_envelope",
            label="Get Envelope",
            method="GET",
            path=_ACCOUNT + "/envelopes/{envelope_id}",
            visible_fields=["envelope_id"],
        ),
        OpSpec(
            id="create_envelope",
            label="Create Envelope (documents + recipients)",
            method="POST",
            path=_ACCOUNT + "/envelopes",
            visible_fields=["email_subject", "email_body", "documents", "recipients", "status"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "emailSubject": getattr(v, "email_subject", None) or "",
                    "emailBlurb": getattr(v, "email_body", None),
                    "documents": getattr(v, "documents", None) or [],
                    "recipients": getattr(v, "recipients", None) or {},
                    "status": getattr(v, "status", None) or "sent",
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="send_from_template",
            label="Send From Template",
            method="POST",
            path=_ACCOUNT + "/envelopes",
            visible_fields=["template_id", "template_roles", "email_subject", "status"],
            body_builder=lambda v: {
                "templateId": getattr(v, "template_id", None) or "",
                "templateRoles": getattr(v, "template_roles", None) or [],
                "emailSubject": getattr(v, "email_subject", None) or "",
                "status": getattr(v, "status", None) or "sent",
            },
        ),
        OpSpec(
            id="void_envelope",
            label="Void Envelope",
            method="PUT",
            path=_ACCOUNT + "/envelopes/{envelope_id}",
            visible_fields=["envelope_id"],
            body_builder=lambda v: {
                "status": "voided",
                "voidedReason": "Voided via RunMyCrew",
            },
        ),
        OpSpec(
            id="list_templates",
            label="List Templates",
            method="GET",
            path=_ACCOUNT + "/templates",
            visible_fields=["count"],
            query_builder=lambda v: {"count": int(getattr(v, "count", 25) or 25)},
        ),
        OpSpec(
            id="get_envelope_recipients",
            label="Get Envelope Recipients",
            method="GET",
            path=_ACCOUNT + "/envelopes/{envelope_id}/recipients",
            visible_fields=["envelope_id"],
        ),
    ],
    outputs_schema=[
        {"label": "envelopeId", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "envelopes", "type": "array"},
        {"label": "envelopeTemplates", "type": "array"},
        {"label": "signers", "type": "array"},
    ],
    allow_error=True,
)
