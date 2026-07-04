"""SAP S/4HANA Cloud action node — SAP S/4HANA Cloud — OData v2 business partners, sales orders, ledger.

REST at https://{host}/sap/opu/odata/sap. See sim-parity roadmap Phase 4-close-5.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.sap_s4hana",
    name="SAP S/4HANA Cloud",
    category="integration",
    description="SAP S/4HANA Cloud — OData v2 business partners, sales orders, ledger.",
    icon_slug="sap_s4hana",
    color="#0FAAFF",
    base_url="https://{host}/sap/opu/odata/sap",
    credential_type="sap_s4hana_credentials",
    token_field=["api_key"],
    auth="basic",
    auth_basic_username="{username}",
    extra_headers={"Accept": "application/json"},
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
        FieldSpec(name="product_id", label="Product ID", type="string"),
        FieldSpec(name="purchase_order", label="Purchase Order ID", type="string"),
    ],
    operations=[
        OpSpec(
            id="list_business_partners",
            label="List Business Partners",
            method="GET",
            path="/API_BUSINESS_PARTNER/A_BusinessPartner",
            visible_fields=["top", "filter"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "$top": int(getattr(v, "top", 20) or 20),
                    "$filter": getattr(v, "filter", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_business_partner",
            label="Get Business Partner",
            method="GET",
            path="/API_BUSINESS_PARTNER/A_BusinessPartner('{business_partner}')",
            visible_fields=["business_partner"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_sales_orders",
            label="List Sales Orders",
            method="GET",
            path="/API_SALES_ORDER_SRV/A_SalesOrder",
            visible_fields=["top", "filter"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "$top": int(getattr(v, "top", 20) or 20),
                    "$filter": getattr(v, "filter", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_sales_order",
            label="Get Sales Order",
            method="GET",
            path="/API_SALES_ORDER_SRV/A_SalesOrder('{sales_order}')",
            visible_fields=["sales_order"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_journal_entries",
            label="List Journal Entries",
            method="GET",
            path="/API_JOURNALENTRYITEMBASIC_SRV/JournalEntryItemBasicSet",
            visible_fields=["top", "filter"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "$top": int(getattr(v, "top", 20) or 20),
                    "$filter": getattr(v, "filter", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="list_products",
            label="List Products",
            method="GET",
            path="/API_PRODUCT_SRV/A_Product",
            visible_fields=["top", "filter"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "$top": int(getattr(v, "top", 20) or 20),
                    "$filter": getattr(v, "filter", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_product",
            label="Get Product",
            method="GET",
            path="/API_PRODUCT_SRV/A_Product('{product_id}')",
            visible_fields=["product_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_purchase_orders",
            label="List Purchase Orders",
            method="GET",
            path="/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder",
            visible_fields=["top", "filter"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "$top": int(getattr(v, "top", 20) or 20),
                    "$filter": getattr(v, "filter", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_purchase_order",
            label="Get Purchase Order",
            method="GET",
            path="/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder('{purchase_order}')",
            visible_fields=["purchase_order"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_billing_documents",
            label="List Billing Documents",
            method="GET",
            path="/API_BILLING_DOCUMENT_SRV/A_BillingDocument",
            visible_fields=["top"],
            query_builder=lambda v: {"$top": int(getattr(v, "top", 20) or 20)},
        ),
        OpSpec(
            id="list_deliveries",
            label="List Deliveries",
            method="GET",
            path="/API_OUTBOUND_DELIVERY_SRV/A_OutbDeliveryHeader",
            visible_fields=["top"],
            query_builder=lambda v: {"$top": int(getattr(v, "top", 20) or 20)},
        ),
        OpSpec(
            id="list_material_movements",
            label="List Material Movements",
            method="GET",
            path="/API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentHeader",
            visible_fields=["top"],
            query_builder=lambda v: {"$top": int(getattr(v, "top", 20) or 20)},
        ),
        OpSpec(
            id="list_bank_accounts",
            label="List Bank Accounts",
            method="GET",
            path="/API_BANKACCOUNT/BankAccount",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_cost_centers",
            label="List Cost Centers",
            method="GET",
            path="/API_COSTCENTER_SRV/A_CostCenter",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_profit_centers",
            label="List Profit Centers",
            method="GET",
            path="/API_PROFITCENTER_SRV/A_ProfitCenter",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
