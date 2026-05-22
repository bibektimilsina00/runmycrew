from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)
STRIPE_API = "https://api.stripe.com/v1"


class StripeProperties(BaseModel):
    credential: str | None = None
    operation: str = "list_payments"
    amount: int | None = None            # in cents
    currency: str = "usd"
    customer_id: str | None = None
    payment_intent_id: str | None = None
    email: str | None = None
    name: str | None = None
    description: str | None = None
    limit: int = 10
    metadata: Any | None = None


class StripeNode(BaseNode[StripeProperties]):
    @classmethod
    def get_properties_model(cls): return StripeProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.stripe",
            name="Stripe",
            category="integration",
            description="Create payments, manage customers, and retrieve billing data from Stripe.",
            icon="si:SiStripe",
            color="#635bff",
            properties=[
                {"name": "credential", "label": "Stripe Secret Key", "type": "credential", "credentialType": "stripe_api_key", "required": True},
                {"name": "operation", "label": "Operation", "type": "options", "default": "list_payments", "options": [
                    {"label": "Create Payment Intent", "value": "create_payment_intent"},
                    {"label": "Get Payment Intent", "value": "get_payment_intent"},
                    {"label": "List Payment Intents", "value": "list_payments"},
                    {"label": "Create Customer", "value": "create_customer"},
                    {"label": "Get Customer", "value": "get_customer"},
                    {"label": "List Customers", "value": "list_customers"},
                    {"label": "Create Refund", "value": "create_refund"},
                    {"label": "List Invoices", "value": "list_invoices"},
                ]},
                {"name": "amount", "label": "Amount (cents)", "type": "number", "required": True, "condition": {"field": "operation", "value": "create_payment_intent"}, "description": "Amount in smallest currency unit (e.g. 1000 = $10.00)"},
                {"name": "currency", "label": "Currency", "type": "string", "default": "usd", "condition": {"field": "operation", "value": "create_payment_intent"}},
                {"name": "payment_intent_id", "label": "Payment Intent ID", "type": "string", "condition": {"field": "operation", "value": ["get_payment_intent", "create_refund"]}},
                {"name": "customer_id", "label": "Customer ID", "type": "string", "condition": {"field": "operation", "value": ["get_customer", "create_payment_intent"]}},
                {"name": "email", "label": "Email", "type": "string", "condition": {"field": "operation", "value": "create_customer"}},
                {"name": "name", "label": "Name", "type": "string", "condition": {"field": "operation", "value": "create_customer"}},
                {"name": "description", "label": "Description", "type": "string", "mode": "advanced", "condition": {"field": "operation", "value": ["create_payment_intent", "create_customer"]}},
                {"name": "limit", "label": "Limit", "type": "number", "default": 10, "mode": "advanced", "condition": {"field": "operation", "value": ["list_payments", "list_customers", "list_invoices"]}},
            ],
            inputs=1, outputs=1,
            outputs_schema=[{"label": "id", "type": "string"}, {"label": "status", "type": "string"}, {"label": "data", "type": "array"}, {"label": "object", "type": "object"}],
            allow_error=True, credential_type="stripe_api_key",
        )

    def _api_key(self) -> str | None:
        if not self.credential: return None
        return self.credential.get("api_key")

    def _auth(self) -> tuple[str, str]:
        return (self._api_key() or "", "")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self._api_key(): return NodeResult(success=False, error="Stripe secret key required.")
        op = self.props.operation
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if op == "create_payment_intent":
                    if not self.props.amount: return NodeResult(success=False, error="Amount required.")
                    data: dict = {"amount": self.props.amount, "currency": self.props.currency}
                    if self.props.customer_id: data["customer"] = self.props.customer_id
                    if self.props.description: data["description"] = self.props.description
                    r = await client.post(f"{STRIPE_API}/payment_intents", auth=self._auth(), data=data)
                    r.raise_for_status(); return NodeResult(success=True, output_data=r.json())

                elif op == "get_payment_intent":
                    if not self.props.payment_intent_id: return NodeResult(success=False, error="Payment Intent ID required.")
                    r = await client.get(f"{STRIPE_API}/payment_intents/{self.props.payment_intent_id}", auth=self._auth())
                    r.raise_for_status(); return NodeResult(success=True, output_data=r.json())

                elif op == "list_payments":
                    r = await client.get(f"{STRIPE_API}/payment_intents", auth=self._auth(), params={"limit": min(self.props.limit, 100)})
                    r.raise_for_status(); d = r.json(); return NodeResult(success=True, output_data={"data": d.get("data", []), "count": len(d.get("data", []))})

                elif op == "create_customer":
                    data = {}
                    if self.props.email: data["email"] = self.props.email
                    if self.props.name: data["name"] = self.props.name
                    if self.props.description: data["description"] = self.props.description
                    r = await client.post(f"{STRIPE_API}/customers", auth=self._auth(), data=data)
                    r.raise_for_status(); return NodeResult(success=True, output_data=r.json())

                elif op == "get_customer":
                    if not self.props.customer_id: return NodeResult(success=False, error="Customer ID required.")
                    r = await client.get(f"{STRIPE_API}/customers/{self.props.customer_id}", auth=self._auth())
                    r.raise_for_status(); return NodeResult(success=True, output_data=r.json())

                elif op == "list_customers":
                    r = await client.get(f"{STRIPE_API}/customers", auth=self._auth(), params={"limit": min(self.props.limit, 100)})
                    r.raise_for_status(); d = r.json(); return NodeResult(success=True, output_data={"data": d.get("data", []), "count": len(d.get("data", []))})

                elif op == "create_refund":
                    if not self.props.payment_intent_id: return NodeResult(success=False, error="Payment Intent ID required.")
                    r = await client.post(f"{STRIPE_API}/refunds", auth=self._auth(), data={"payment_intent": self.props.payment_intent_id})
                    r.raise_for_status(); return NodeResult(success=True, output_data=r.json())

                elif op == "list_invoices":
                    params: dict = {"limit": min(self.props.limit, 100)}
                    if self.props.customer_id: params["customer"] = self.props.customer_id
                    r = await client.get(f"{STRIPE_API}/invoices", auth=self._auth(), params=params)
                    r.raise_for_status(); d = r.json(); return NodeResult(success=True, output_data={"data": d.get("data", []), "count": len(d.get("data", []))})

                else:
                    return NodeResult(success=False, error=f"Unknown operation: {op}")

        except httpx.HTTPStatusError as e:
            return NodeResult(success=False, error=f"Stripe API {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            logger.error(f"StripeNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))
