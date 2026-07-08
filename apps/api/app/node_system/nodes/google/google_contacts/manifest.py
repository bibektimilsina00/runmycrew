"""Google Contacts action node — Google Contacts — read + write People API contacts.

REST at https://people.googleapis.com/v1. See sim-parity roadmap Phase 4-close-5.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.google_contacts",
    name="Google Contacts",
    category="integration",
    description="Google Contacts — read + write People API contacts.",
    icon_slug="google_contacts",
    color="#ffffff",
    base_url="https://people.googleapis.com/v1",
    credential_type="google_oauth",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="model", label="Model", type="string"),
        FieldSpec(name="messages", label="Messages (JSON array)", type="json", default=[]),
        FieldSpec(name="temperature", label="Temperature", type="number", default=1),
        FieldSpec(name="max_tokens", label="Max Tokens", type="number", default=0),
        FieldSpec(name="input", label="Input", type="string"),
        FieldSpec(name="instructions", label="Instructions", type="string"),
        FieldSpec(name="prompt", label="Prompt", type="string"),
        FieldSpec(name="size", label="Size", type="string", default="1024x1024"),
        FieldSpec(name="quality", label="Quality", type="string", default="high"),
        FieldSpec(name="n", label="Count", type="number", default=1),
        FieldSpec(name="file_url", label="File URL", type="string"),
        FieldSpec(name="image_url", label="Image URL", type="string"),
        FieldSpec(name="mask_url", label="Mask URL", type="string"),
        FieldSpec(name="voice_id", label="Voice ID", type="string"),
        FieldSpec(name="text", label="Text", type="string"),
        FieldSpec(name="model_id", label="Model ID", type="string"),
        FieldSpec(name="user_id", label="User ID", type="string"),
        FieldSpec(name="memory_id", label="Memory ID", type="string"),
        FieldSpec(name="metadata", label="Metadata (JSON)", type="json", default={}),
        FieldSpec(name="query", label="Query", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=10, mode="advanced"),
        FieldSpec(name="session_id", label="Session ID", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="first_name", label="First Name", type="string"),
        FieldSpec(name="last_name", label="Last Name", type="string"),
        FieldSpec(name="task_spec", label="Task Spec (JSON)", type="json", default={}),
        FieldSpec(name="processor", label="Processor", type="string", default="core"),
        FieldSpec(name="input_data", label="Input Data (JSON)", type="json", default={}),
        FieldSpec(name="run_id", label="Run ID", type="string"),
        FieldSpec(name="objective", label="Objective", type="string"),
        FieldSpec(name="page_size", label="Page Size", type="number", default=100),
        FieldSpec(
            name="person_fields",
            label="Person Fields",
            type="string",
            default="names,emailAddresses,phoneNumbers",
        ),
        FieldSpec(name="resource_name", label="Resource Name", type="string"),
        FieldSpec(name="given_name", label="Given Name", type="string"),
        FieldSpec(name="family_name", label="Family Name", type="string"),
        FieldSpec(name="phone", label="Phone", type="string"),
        FieldSpec(name="engine_id", label="Search Engine ID (cx)", type="string"),
        FieldSpec(name="num", label="Num Results", type="number", default=10),
        FieldSpec(name="start", label="Start Index", type="number", default=1),
        FieldSpec(name="search_type", label="Search Type (image or blank)", type="string"),
        FieldSpec(name="to", label="To", type="string"),
        FieldSpec(name="from_number", label="From", type="string"),
        FieldSpec(name="body_text", label="Body Text", type="string"),
        FieldSpec(name="media_url", label="Media URL", type="string"),
        FieldSpec(name="message_sid", label="Message SID", type="string"),
        FieldSpec(name="application_id", label="Application ID", type="string"),
        FieldSpec(name="environment_id", label="Environment ID", type="string"),
        FieldSpec(name="profile_id", label="Configuration Profile ID", type="string"),
        FieldSpec(name="version_number", label="Version Number", type="string"),
        FieldSpec(name="deployment_strategy_id", label="Deployment Strategy ID", type="string"),
        FieldSpec(name="visitor_id", label="Visitor ID", type="string"),
        FieldSpec(name="since", label="Since (ISO)", type="string"),
        FieldSpec(name="host", label="SAP Host", type="string"),
        FieldSpec(name="username", label="Username", type="string"),
        FieldSpec(name="business_partner", label="Business Partner ID", type="string"),
        FieldSpec(name="sales_order", label="Sales Order ID", type="string"),
        FieldSpec(name="top", label="Top", type="number", default=20, mode="advanced"),
        FieldSpec(name="filter", label="Filter", type="string", mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_contacts",
            label="List Contacts",
            method="GET",
            path="/people/me/connections",
            visible_fields=["page_size", "person_fields"],
            query_builder=lambda v: {
                "pageSize": int(getattr(v, "page_size", 100) or 100),
                "personFields": getattr(v, "person_fields", None)
                or "names,emailAddresses,phoneNumbers",
            },
        ),
        OpSpec(
            id="get_contact",
            label="Get Contact",
            method="GET",
            path="/{resource_name}",
            visible_fields=["resource_name", "person_fields"],
            query_builder=lambda v: {
                "personFields": getattr(v, "person_fields", None)
                or "names,emailAddresses,phoneNumbers"
            },
        ),
        OpSpec(
            id="create_contact",
            label="Create Contact",
            method="POST",
            path="/people:createContact",
            visible_fields=["given_name", "family_name", "email", "phone"],
            body_builder=lambda v: {
                "names": [
                    {
                        "givenName": getattr(v, "given_name", None) or None,
                        "familyName": getattr(v, "family_name", None) or None,
                    }
                ],
                "emailAddresses": (
                    [{"value": getattr(v, "email", None) or None}]
                    if getattr(v, "email", None)
                    else []
                ),
                "phoneNumbers": (
                    [{"value": getattr(v, "phone", None) or None}]
                    if getattr(v, "phone", None)
                    else []
                ),
            },
        ),
        OpSpec(
            id="update_contact",
            label="Update Contact",
            method="PATCH",
            path="/{resource_name}:updateContact",
            visible_fields=["resource_name", "given_name", "family_name", "email", "phone"],
            body_builder=lambda v: {
                "names": [
                    {
                        "givenName": getattr(v, "given_name", None) or None,
                        "familyName": getattr(v, "family_name", None) or None,
                    }
                ],
                "emailAddresses": (
                    [{"value": getattr(v, "email", None) or None}]
                    if getattr(v, "email", None)
                    else []
                ),
                "phoneNumbers": (
                    [{"value": getattr(v, "phone", None) or None}]
                    if getattr(v, "phone", None)
                    else []
                ),
            },
        ),
        OpSpec(
            id="delete_contact",
            label="Delete Contact",
            method="DELETE",
            path="/{resource_name}:deleteContact",
            visible_fields=["resource_name"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="search_contacts",
            label="Search Contacts",
            method="GET",
            path="/people:searchContacts",
            visible_fields=["query"],
            query_builder=lambda v: {
                "query": getattr(v, "query", "") or "",
                "readMask": "names,emailAddresses,phoneNumbers",
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
