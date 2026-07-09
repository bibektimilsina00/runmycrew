"""Stripe action node — manifest form.

Stripe REST API v1 at `https://api.stripe.com/v1`. Auth is HTTP Basic
with the API key as the username and an empty password — the scaffold
`basic_token_only` scheme covers this exact case.

Payloads to Stripe are `application/x-www-form-urlencoded`, not JSON.
The scaffold auto-detects that when `content_type` on the manifest is
`form`. We set it and every body_builder returns a flat dict of scalar
values (Stripe accepts nested via bracket notation but we don't need
that for the surface we ship).

"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)

MANIFEST = ProviderManifest(
    type="action.stripe",
    name="Stripe",
    category="integration",
    description="Stripe — payments, customers, subscriptions, invoices, refunds.",
    icon_slug="stripe",
    color="#ffffff",
    base_url="https://api.stripe.com/v1",
    credential_type="stripe_api_key",
    token_field=["api_key"],
    auth="basic_token_only",
    content_type="application/x-www-form-urlencoded",
    fields=[
        FieldSpec(name="amount", label="Amount (cents)", type="number"),
        FieldSpec(name="currency", label="Currency", type="string", default="usd"),
        FieldSpec(name="description", label="Description", type="string"),
        FieldSpec(name="payment_intent_id", label="Payment Intent ID", type="string"),
        FieldSpec(
            name="customer_id",
            label="Customer",
            type="string",
            remote=RemoteLookup(provider="stripe", resource="customers"),
        ),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="name", label="Name", type="string"),
        FieldSpec(name="refund_amount", label="Refund Amount (cents)", type="number"),
        FieldSpec(name="invoice_id", label="Invoice ID", type="string"),
        FieldSpec(name="charge_id", label="Charge ID", type="string"),
        FieldSpec(name="subscription_id", label="Subscription ID", type="string"),
        FieldSpec(
            name="price_id",
            label="Price",
            type="string",
            remote=RemoteLookup(
                provider="stripe",
                resource="prices",
                params={"product_id": "${product_id}"},
                depends_on=["product_id"],
            ),
        ),
        FieldSpec(
            name="product_id",
            label="Product",
            type="string",
            remote=RemoteLookup(provider="stripe", resource="products"),
        ),
        FieldSpec(name="product_name", label="Product Name", type="string"),
        FieldSpec(name="price_amount", label="Price Amount (cents)", type="number"),
        FieldSpec(
            name="recurring_interval",
            label="Recurring Interval (month|year|week|day)",
            type="string",
        ),
        FieldSpec(name="payment_method_id", label="Payment Method ID", type="string"),
        FieldSpec(name="checkout_success_url", label="Checkout Success URL", type="string"),
        FieldSpec(name="checkout_cancel_url", label="Checkout Cancel URL", type="string"),
        FieldSpec(
            name="checkout_mode",
            label="Checkout Mode (payment|subscription|setup)",
            type="string",
            default="payment",
        ),
        FieldSpec(name="limit", label="Limit", type="number", default=10, mode="advanced"),
        FieldSpec(
            name="starting_after", label="Starting After (cursor)", type="string", mode="advanced"
        ),
        FieldSpec(name="event_id", label="Event ID", type="string"),
        FieldSpec(name="balance_transaction_id", label="Balance Transaction ID", type="string"),
        FieldSpec(name="dispute_id", label="Dispute ID", type="string"),
        FieldSpec(name="coupon_id", label="Coupon ID", type="string"),
        FieldSpec(name="percent_off", label="Percent Off", type="number"),
        FieldSpec(
            name="duration",
            label="Duration (once|forever|repeating)",
            type="string",
            default="once",
        ),
        FieldSpec(name="type_field", label="Payment Method Type", type="string", default="card"),
        FieldSpec(name="setup_intent_id", label="Setup Intent ID", type="string"),
        FieldSpec(name="destination", label="Destination Account ID", type="string"),
    ],
    operations=[
        OpSpec(
            id="create_payment_intent",
            label="Create Payment Intent",
            method="POST",
            path="/payment_intents",
            visible_fields=["amount", "currency", "customer_id", "description"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "amount": int(getattr(v, "amount", 0) or 0),
                    "currency": getattr(v, "currency", None) or "usd",
                    "customer": getattr(v, "customer_id", None) or None,
                    "description": getattr(v, "description", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_payment_intent",
            label="Get Payment Intent",
            method="GET",
            path="/payment_intents/{payment_intent_id}",
            visible_fields=["payment_intent_id"],
        ),
        OpSpec(
            id="list_payments",
            label="List Payment Intents",
            method="GET",
            path="/payment_intents",
            visible_fields=["customer_id", "limit"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "customer": getattr(v, "customer_id", None) or None,
                    "limit": int(getattr(v, "limit", 10) or 10),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="create_customer",
            label="Create Customer",
            method="POST",
            path="/customers",
            visible_fields=["email", "name", "description"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "email": getattr(v, "email", None) or None,
                    "name": getattr(v, "name", None) or None,
                    "description": getattr(v, "description", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_customer",
            label="Get Customer",
            method="GET",
            path="/customers/{customer_id}",
            visible_fields=["customer_id"],
        ),
        OpSpec(
            id="list_customers",
            label="List Customers",
            method="GET",
            path="/customers",
            visible_fields=["email", "limit"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "email": getattr(v, "email", None) or None,
                    "limit": int(getattr(v, "limit", 10) or 10),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="create_refund",
            label="Create Refund",
            method="POST",
            path="/refunds",
            visible_fields=["payment_intent_id", "refund_amount"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "payment_intent": getattr(v, "payment_intent_id", "") or "",
                    "amount": int(getattr(v, "refund_amount", 0) or 0) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="list_invoices",
            label="List Invoices",
            method="GET",
            path="/invoices",
            visible_fields=["customer_id", "limit"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "customer": getattr(v, "customer_id", None) or None,
                    "limit": int(getattr(v, "limit", 10) or 10),
                }.items()
                if val is not None
            },
        ),
        # ─── customer depth ───────────────────────────────────────
        OpSpec(
            id="update_customer",
            label="Update Customer",
            method="POST",
            path="/customers/{customer_id}",
            visible_fields=["customer_id", "email", "name", "description"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "email": getattr(v, "email", None) or None,
                    "name": getattr(v, "name", None) or None,
                    "description": getattr(v, "description", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="delete_customer",
            label="Delete Customer",
            method="DELETE",
            path="/customers/{customer_id}",
            visible_fields=["customer_id"],
        ),
        # ─── payment intent depth ──────────────────────────────────
        OpSpec(
            id="confirm_payment_intent",
            label="Confirm Payment Intent",
            method="POST",
            path="/payment_intents/{payment_intent_id}/confirm",
            visible_fields=["payment_intent_id", "payment_method_id"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "payment_method": getattr(v, "payment_method_id", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="capture_payment_intent",
            label="Capture Payment Intent",
            method="POST",
            path="/payment_intents/{payment_intent_id}/capture",
            visible_fields=["payment_intent_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="cancel_payment_intent",
            label="Cancel Payment Intent",
            method="POST",
            path="/payment_intents/{payment_intent_id}/cancel",
            visible_fields=["payment_intent_id"],
            body_builder=lambda v: {},
        ),
        # ─── charges ───────────────────────────────────────────────
        OpSpec(
            id="get_charge",
            label="Get Charge",
            method="GET",
            path="/charges/{charge_id}",
            visible_fields=["charge_id"],
        ),
        OpSpec(
            id="list_charges",
            label="List Charges",
            method="GET",
            path="/charges",
            visible_fields=["customer_id", "limit"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "customer": getattr(v, "customer_id", None) or None,
                    "limit": int(getattr(v, "limit", 10) or 10),
                }.items()
                if val is not None
            },
        ),
        # ─── invoices ──────────────────────────────────────────────
        OpSpec(
            id="get_invoice",
            label="Get Invoice",
            method="GET",
            path="/invoices/{invoice_id}",
            visible_fields=["invoice_id"],
        ),
        OpSpec(
            id="create_invoice",
            label="Create Invoice (draft)",
            method="POST",
            path="/invoices",
            visible_fields=["customer_id", "description"],
            body_builder=lambda v: {
                "customer": getattr(v, "customer_id", "") or "",
                "description": getattr(v, "description", None) or None,
            },
        ),
        OpSpec(
            id="finalize_invoice",
            label="Finalize Invoice",
            method="POST",
            path="/invoices/{invoice_id}/finalize",
            visible_fields=["invoice_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="pay_invoice",
            label="Pay Invoice",
            method="POST",
            path="/invoices/{invoice_id}/pay",
            visible_fields=["invoice_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="send_invoice",
            label="Send Invoice",
            method="POST",
            path="/invoices/{invoice_id}/send",
            visible_fields=["invoice_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="void_invoice",
            label="Void Invoice",
            method="POST",
            path="/invoices/{invoice_id}/void",
            visible_fields=["invoice_id"],
            body_builder=lambda v: {},
        ),
        # ─── subscriptions ─────────────────────────────────────────
        OpSpec(
            id="create_subscription",
            label="Create Subscription",
            method="POST",
            path="/subscriptions",
            visible_fields=["customer_id", "price_id"],
            body_builder=lambda v: {
                "customer": getattr(v, "customer_id", "") or "",
                "items[0][price]": getattr(v, "price_id", "") or "",
            },
        ),
        OpSpec(
            id="get_subscription",
            label="Get Subscription",
            method="GET",
            path="/subscriptions/{subscription_id}",
            visible_fields=["subscription_id"],
        ),
        OpSpec(
            id="list_subscriptions",
            label="List Subscriptions",
            method="GET",
            path="/subscriptions",
            visible_fields=["customer_id", "limit"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "customer": getattr(v, "customer_id", None) or None,
                    "limit": int(getattr(v, "limit", 10) or 10),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="cancel_subscription",
            label="Cancel Subscription",
            method="DELETE",
            path="/subscriptions/{subscription_id}",
            visible_fields=["subscription_id"],
        ),
        # ─── products + prices ─────────────────────────────────────
        OpSpec(
            id="create_product",
            label="Create Product",
            method="POST",
            path="/products",
            visible_fields=["product_name", "description"],
            body_builder=lambda v: {
                "name": getattr(v, "product_name", "") or "",
                "description": getattr(v, "description", None) or None,
            },
        ),
        OpSpec(
            id="list_products",
            label="List Products",
            method="GET",
            path="/products",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 10) or 10)},
        ),
        OpSpec(
            id="create_price",
            label="Create Price",
            method="POST",
            path="/prices",
            visible_fields=["product_id", "price_amount", "currency", "recurring_interval"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "product": getattr(v, "product_id", "") or "",
                    "unit_amount": int(getattr(v, "price_amount", 0) or 0),
                    "currency": getattr(v, "currency", None) or "usd",
                    "recurring[interval]": getattr(v, "recurring_interval", None) or None,
                }.items()
                if val is not None
            },
        ),
        # ─── checkout + billing portal ─────────────────────────────
        OpSpec(
            id="create_checkout_session",
            label="Create Checkout Session",
            method="POST",
            path="/checkout/sessions",
            visible_fields=[
                "checkout_mode",
                "price_id",
                "customer_id",
                "checkout_success_url",
                "checkout_cancel_url",
            ],
            body_builder=lambda v: {
                "mode": getattr(v, "checkout_mode", None) or "payment",
                "line_items[0][price]": getattr(v, "price_id", "") or "",
                "line_items[0][quantity]": 1,
                "success_url": getattr(v, "checkout_success_url", "") or "",
                "cancel_url": getattr(v, "checkout_cancel_url", "") or "",
                "customer": getattr(v, "customer_id", None) or None,
            },
        ),
        OpSpec(
            id="create_billing_portal_session",
            label="Create Billing Portal Session",
            method="POST",
            path="/billing_portal/sessions",
            visible_fields=["customer_id", "checkout_success_url"],
            body_builder=lambda v: {
                "customer": getattr(v, "customer_id", "") or "",
                "return_url": getattr(v, "checkout_success_url", "") or "",
            },
        ),
        # ─── events + disputes + coupons ───────────────────────────
        OpSpec(
            id="get_event",
            label="Get Event",
            method="GET",
            path="/events/{event_id}",
            visible_fields=["event_id"],
        ),
        OpSpec(
            id="list_events",
            label="List Events",
            method="GET",
            path="/events",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 10) or 10)},
        ),
        OpSpec(
            id="get_dispute",
            label="Get Dispute",
            method="GET",
            path="/disputes/{dispute_id}",
            visible_fields=["dispute_id"],
        ),
        OpSpec(
            id="list_disputes",
            label="List Disputes",
            method="GET",
            path="/disputes",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 10) or 10)},
        ),
        OpSpec(
            id="create_coupon",
            label="Create Coupon",
            method="POST",
            path="/coupons",
            visible_fields=["coupon_id", "percent_off", "duration"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "id": getattr(v, "coupon_id", None) or None,
                    "percent_off": int(getattr(v, "percent_off", 0) or 0) or None,
                    "duration": getattr(v, "duration", None) or "once",
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="list_coupons",
            label="List Coupons",
            method="GET",
            path="/coupons",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 10) or 10)},
        ),
        OpSpec(
            id="delete_coupon",
            label="Delete Coupon",
            method="DELETE",
            path="/coupons/{coupon_id}",
            visible_fields=["coupon_id"],
        ),
        OpSpec(
            id="list_payment_methods",
            label="List Customer Payment Methods",
            method="GET",
            path="/payment_methods",
            visible_fields=["customer_id", "type_field"],
            query_builder=lambda v: {
                "customer": getattr(v, "customer_id", "") or "",
                "type": getattr(v, "type_field", None) or "card",
            },
        ),
        OpSpec(
            id="attach_payment_method",
            label="Attach Payment Method to Customer",
            method="POST",
            path="/payment_methods/{payment_method_id}/attach",
            visible_fields=["payment_method_id", "customer_id"],
            body_builder=lambda v: {"customer": getattr(v, "customer_id", "") or ""},
        ),
        OpSpec(
            id="detach_payment_method",
            label="Detach Payment Method",
            method="POST",
            path="/payment_methods/{payment_method_id}/detach",
            visible_fields=["payment_method_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="list_setup_intents",
            label="List Setup Intents",
            method="GET",
            path="/setup_intents",
            visible_fields=["customer_id"],
            query_builder=lambda v: {
                k: val
                for k, val in {"customer": getattr(v, "customer_id", None) or None}.items()
                if val
            },
        ),
        OpSpec(
            id="create_setup_intent",
            label="Create Setup Intent",
            method="POST",
            path="/setup_intents",
            visible_fields=["customer_id"],
            body_builder=lambda v: {
                k: val
                for k, val in {"customer": getattr(v, "customer_id", None) or None}.items()
                if val
            },
        ),
        OpSpec(
            id="confirm_setup_intent",
            label="Confirm Setup Intent",
            method="POST",
            path="/setup_intents/{setup_intent_id}/confirm",
            visible_fields=["setup_intent_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="cancel_setup_intent",
            label="Cancel Setup Intent",
            method="POST",
            path="/setup_intents/{setup_intent_id}/cancel",
            visible_fields=["setup_intent_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="list_transfers",
            label="List Transfers",
            method="GET",
            path="/transfers",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_transfer",
            label="Create Transfer",
            method="POST",
            path="/transfers",
            visible_fields=["amount", "currency", "destination"],
            body_builder=lambda v: {
                "amount": int(getattr(v, "amount", 0) or 0),
                "currency": getattr(v, "currency", None) or "usd",
                "destination": getattr(v, "destination", "") or "",
            },
        ),
        OpSpec(
            id="list_payouts",
            label="List Payouts",
            method="GET",
            path="/payouts",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_payout",
            label="Create Payout",
            method="POST",
            path="/payouts",
            visible_fields=["amount", "currency"],
            body_builder=lambda v: {
                "amount": int(getattr(v, "amount", 0) or 0),
                "currency": getattr(v, "currency", None) or "usd",
            },
        ),
        OpSpec(
            id="list_balance_transactions",
            label="List Balance Transactions",
            method="GET",
            path="/balance_transactions",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_balance",
            label="Get Balance",
            method="GET",
            path="/balance",
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
