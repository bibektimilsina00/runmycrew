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
HUBSPOT_API = "https://api.hubapi.com"


class HubSpotProperties(BaseModel):
    credential: str | None = None
    operation: str = "list_contacts"
    contact_id: str | None = None
    deal_id: str | None = None
    company_id: str | None = None
    email: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    phone: str | None = None
    properties: Any | None = None  # dict of HubSpot properties
    deal_name: str | None = None
    deal_stage: str | None = None
    amount: str | None = None
    limit: int = 10
    search_query: str | None = None


class HubSpotNode(BaseNode[HubSpotProperties]):
    @classmethod
    def get_properties_model(cls):
        return HubSpotProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.hubspot",
            name="HubSpot",
            category="integration",
            description="Manage contacts, deals, and companies in HubSpot CRM.",
            icon="hubspot",
            color="#1c1c1c",
            properties=[
                {
                    "name": "credential",
                    "label": "HubSpot Token",
                    "type": "credential",
                    "credentialType": "hubspot_api_key",
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "list_contacts",
                    "options": [
                        {"label": "List Contacts", "value": "list_contacts"},
                        {"label": "Get Contact", "value": "get_contact"},
                        {"label": "Create Contact", "value": "create_contact"},
                        {"label": "Update Contact", "value": "update_contact"},
                        {"label": "Search Contacts", "value": "search_contacts"},
                        {"label": "Create Deal", "value": "create_deal"},
                        {"label": "Get Deal", "value": "get_deal"},
                        {"label": "List Deals", "value": "list_deals"},
                        {"label": "Create Company", "value": "create_company"},
                        {"label": "List Companies", "value": "list_companies"},
                    ],
                },
                # Contact ops
                {
                    "name": "contact_id",
                    "label": "Contact ID",
                    "type": "string",
                    "condition": {"field": "operation", "value": ["get_contact", "update_contact"]},
                },
                {
                    "name": "email",
                    "label": "Email",
                    "type": "string",
                    "condition": {
                        "field": "operation",
                        "value": ["create_contact", "update_contact"],
                    },
                },
                {
                    "name": "firstname",
                    "label": "First Name",
                    "type": "string",
                    "condition": {
                        "field": "operation",
                        "value": ["create_contact", "update_contact"],
                    },
                },
                {
                    "name": "lastname",
                    "label": "Last Name",
                    "type": "string",
                    "condition": {
                        "field": "operation",
                        "value": ["create_contact", "update_contact"],
                    },
                },
                {
                    "name": "phone",
                    "label": "Phone",
                    "type": "string",
                    "mode": "advanced",
                    "condition": {
                        "field": "operation",
                        "value": ["create_contact", "update_contact"],
                    },
                },
                {
                    "name": "search_query",
                    "label": "Search Query",
                    "type": "string",
                    "condition": {"field": "operation", "value": "search_contacts"},
                    "placeholder": "John Doe",
                },
                # Deal ops
                {
                    "name": "deal_id",
                    "label": "Deal ID",
                    "type": "string",
                    "condition": {"field": "operation", "value": "get_deal"},
                },
                {
                    "name": "deal_name",
                    "label": "Deal Name",
                    "type": "string",
                    "condition": {"field": "operation", "value": "create_deal"},
                },
                {
                    "name": "deal_stage",
                    "label": "Deal Stage",
                    "type": "string",
                    "default": "appointmentscheduled",
                    "condition": {"field": "operation", "value": "create_deal"},
                },
                {
                    "name": "amount",
                    "label": "Amount",
                    "type": "string",
                    "mode": "advanced",
                    "condition": {"field": "operation", "value": "create_deal"},
                },
                # Company ops
                {
                    "name": "properties",
                    "label": "Properties (JSON)",
                    "type": "json",
                    "mode": "advanced",
                    "condition": {"field": "operation", "value": "create_company"},
                    "placeholder": '{"name": "Acme Corp", "domain": "acme.com"}',
                },
                # Shared
                {
                    "name": "limit",
                    "label": "Limit",
                    "type": "number",
                    "default": 10,
                    "mode": "advanced",
                    "condition": {
                        "field": "operation",
                        "value": ["list_contacts", "list_deals", "list_companies"],
                    },
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "results", "type": "array"},
                {"label": "id", "type": "string"},
                {"label": "properties", "type": "object"},
                {"label": "total", "type": "number"},
            ],
            allow_error=True,
            credential_type="hubspot_api_key",
        )

    def _api_key(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("api_key")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._api_key()}", "Content-Type": "application/json"}

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self._api_key():
            return NodeResult(success=False, error="HubSpot token required.")
        op = self.props.operation
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if op == "list_contacts":
                    r = await client.get(
                        f"{HUBSPOT_API}/crm/v3/objects/contacts",
                        headers=self._headers(),
                        params={"limit": min(self.props.limit, 100)},
                    )
                    r.raise_for_status()
                    d = r.json()
                    return NodeResult(
                        success=True,
                        output_data={"results": d.get("results", []), "total": d.get("total", 0)},
                    )

                elif op == "get_contact":
                    if not self.props.contact_id:
                        return NodeResult(success=False, error="Contact ID required.")
                    r = await client.get(
                        f"{HUBSPOT_API}/crm/v3/objects/contacts/{self.props.contact_id}",
                        headers=self._headers(),
                    )
                    r.raise_for_status()
                    return NodeResult(success=True, output_data=r.json())

                elif op == "create_contact":
                    props: dict = {}
                    if self.props.email:
                        props["email"] = self.props.email
                    if self.props.firstname:
                        props["firstname"] = self.props.firstname
                    if self.props.lastname:
                        props["lastname"] = self.props.lastname
                    if self.props.phone:
                        props["phone"] = self.props.phone
                    r = await client.post(
                        f"{HUBSPOT_API}/crm/v3/objects/contacts",
                        headers=self._headers(),
                        json={"properties": props},
                    )
                    r.raise_for_status()
                    rec = r.json()
                    return NodeResult(
                        success=True,
                        output_data={"id": rec.get("id"), "properties": rec.get("properties", {})},
                    )

                elif op == "update_contact":
                    if not self.props.contact_id:
                        return NodeResult(success=False, error="Contact ID required.")
                    props = {}
                    if self.props.email:
                        props["email"] = self.props.email
                    if self.props.firstname:
                        props["firstname"] = self.props.firstname
                    if self.props.lastname:
                        props["lastname"] = self.props.lastname
                    if self.props.phone:
                        props["phone"] = self.props.phone
                    r = await client.patch(
                        f"{HUBSPOT_API}/crm/v3/objects/contacts/{self.props.contact_id}",
                        headers=self._headers(),
                        json={"properties": props},
                    )
                    r.raise_for_status()
                    return NodeResult(success=True, output_data=r.json())

                elif op == "search_contacts":
                    body: dict = {
                        "query": self.props.search_query or "",
                        "limit": min(self.props.limit, 100),
                    }
                    r = await client.post(
                        f"{HUBSPOT_API}/crm/v3/objects/contacts/search",
                        headers=self._headers(),
                        json=body,
                    )
                    r.raise_for_status()
                    d = r.json()
                    return NodeResult(
                        success=True,
                        output_data={"results": d.get("results", []), "total": d.get("total", 0)},
                    )

                elif op == "create_deal":
                    if not self.props.deal_name:
                        return NodeResult(success=False, error="Deal name required.")
                    props = {
                        "dealname": self.props.deal_name,
                        "dealstage": self.props.deal_stage or "appointmentscheduled",
                    }
                    if self.props.amount:
                        props["amount"] = self.props.amount
                    r = await client.post(
                        f"{HUBSPOT_API}/crm/v3/objects/deals",
                        headers=self._headers(),
                        json={"properties": props},
                    )
                    r.raise_for_status()
                    rec = r.json()
                    return NodeResult(
                        success=True,
                        output_data={"id": rec.get("id"), "properties": rec.get("properties", {})},
                    )

                elif op == "get_deal":
                    if not self.props.deal_id:
                        return NodeResult(success=False, error="Deal ID required.")
                    r = await client.get(
                        f"{HUBSPOT_API}/crm/v3/objects/deals/{self.props.deal_id}",
                        headers=self._headers(),
                    )
                    r.raise_for_status()
                    return NodeResult(success=True, output_data=r.json())

                elif op == "list_deals":
                    r = await client.get(
                        f"{HUBSPOT_API}/crm/v3/objects/deals",
                        headers=self._headers(),
                        params={"limit": min(self.props.limit, 100)},
                    )
                    r.raise_for_status()
                    d = r.json()
                    return NodeResult(
                        success=True,
                        output_data={"results": d.get("results", []), "total": d.get("total", 0)},
                    )

                elif op == "create_company":
                    props = self.props.properties or {}
                    r = await client.post(
                        f"{HUBSPOT_API}/crm/v3/objects/companies",
                        headers=self._headers(),
                        json={"properties": props},
                    )
                    r.raise_for_status()
                    rec = r.json()
                    return NodeResult(
                        success=True,
                        output_data={"id": rec.get("id"), "properties": rec.get("properties", {})},
                    )

                elif op == "list_companies":
                    r = await client.get(
                        f"{HUBSPOT_API}/crm/v3/objects/companies",
                        headers=self._headers(),
                        params={"limit": min(self.props.limit, 100)},
                    )
                    r.raise_for_status()
                    d = r.json()
                    return NodeResult(
                        success=True,
                        output_data={"results": d.get("results", []), "total": d.get("total", 0)},
                    )

                else:
                    return NodeResult(success=False, error=f"Unknown operation: {op}")

        except httpx.HTTPStatusError as e:
            return NodeResult(
                success=False,
                error=f"HubSpot API {e.response.status_code}: {e.response.text[:200]}",
            )
        except Exception as e:
            logger.error(f"HubSpotNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))
