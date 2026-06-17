"""Google Contacts (People API) action node — 13 ops.

Contact CRUD
  - `create_contact` / `get_contact`
  - `update_contact` / `delete_contact`

Search / list
  - `list_contacts` / `search_contacts`
  - `list_other_contacts`

Groups (labels)
  - `list_groups`       / `create_group`     / `delete_group`
  - `add_to_group`      / `remove_from_group`

OAuth scope: `contacts` (already in GoogleOAuthProvider).
"""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, field_validator

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

PEOPLE_API = "https://people.googleapis.com/v1"

# Default `personFields` mask — covers what 99% of automations actually
# read. Power users can extend via `person_fields` field.
DEFAULT_PERSON_FIELDS = (
    "names,emailAddresses,phoneNumbers,addresses,organizations,biographies,"
    "birthdays,urls,photos,memberships,metadata"
)


class GooglePeopleProperties(BaseModel):
    credential: str | None = None
    operation: str = "list_contacts"

    # contact identity
    resource_name: str | None = None  # e.g. "people/c123…"

    # create / update fields — all optional; only non-empty ones get sent
    given_name: str | None = None
    family_name: str | None = None
    emails: Any = None  # list[str] or list[{value, type}]
    phones: Any = None  # list[str] or list[{value, type}]
    addresses: Any = None  # list[str] (formatted) or list[{streetAddress, city, region, postalCode, country, type}]
    organization_name: str | None = None
    organization_title: str | None = None
    biography: Any = None  # accept any to allow template interpolation
    birthday: str | None = None  # YYYY-MM-DD
    urls: Any = None  # list[str]

    # list / search
    query: str | None = None
    page_size: int = 100
    page_token: str | None = None
    person_fields: str = DEFAULT_PERSON_FIELDS
    sort_order: str = "LAST_MODIFIED_DESCENDING"  # FIRST_NAME_ASCENDING / LAST_NAME_ASCENDING / LAST_MODIFIED_DESCENDING

    # group ops
    group_resource_name: str | None = None
    group_name: str | None = None
    contact_resource_names: Any = None  # list[str] of people/c… ids

    @field_validator("resource_name", "group_resource_name", mode="before")
    @classmethod
    def _coerce_resource_name(cls, value: Any) -> str | None:
        # Picker may emit `{id, name}` or `{resourceName, title}` — collapse
        # to the bare string the API needs.
        if isinstance(value, dict):
            v = value.get("resourceName") or value.get("id")
            return str(v) if isinstance(v, str) and v else None
        if value in (None, ""):
            return None
        return str(value)


def _cond(op: str) -> dict[str, Any]:
    return {"field": "operation", "value": op}


def _cond_any(*ops: str) -> dict[str, Any]:
    return {"field": "operation", "value": list(ops)}


_CONTACT_OPS = (
    "get_contact",
    "update_contact",
    "delete_contact",
)
_CREATE_UPDATE_OPS = ("create_contact", "update_contact")


class GooglePeopleNode(BaseNode[GooglePeopleProperties]):
    @classmethod
    def get_properties_model(cls):
        return GooglePeopleProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.gpeople",
            name="Google Contacts",
            category="integration",
            description=(
                "Manage Google Contacts via the People API — create, search, "
                "tag with groups, and pull individual or batched contact "
                "records."
            ),
            icon="si:SiGooglecontacts",
            color="#1a73e8",
            properties=[
                {
                    "name": "credential",
                    "label": "Google Account",
                    "type": "credential",
                    "credentialType": "google_oauth",
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "list_contacts",
                    "options": [
                        {"label": "List Contacts", "value": "list_contacts"},
                        {"label": "Search Contacts", "value": "search_contacts"},
                        {"label": "Get Contact", "value": "get_contact"},
                        {"label": "Create Contact", "value": "create_contact"},
                        {"label": "Update Contact", "value": "update_contact"},
                        {"label": "Delete Contact", "value": "delete_contact"},
                        {"label": "List Other Contacts", "value": "list_other_contacts"},
                        {"label": "List Groups (Labels)", "value": "list_groups"},
                        {"label": "Create Group", "value": "create_group"},
                        {"label": "Delete Group", "value": "delete_group"},
                        {"label": "Add to Group", "value": "add_to_group"},
                        {"label": "Remove from Group", "value": "remove_from_group"},
                    ],
                },
                # ── resource_name ──────────────────────────────────────
                {
                    "name": "resource_name",
                    "label": "Contact ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "people/c12345…  or  {{ $trigger.resource_name }}",
                    "description": "Use the People API resource name (`people/c…`).",
                    "condition": _cond_any(*_CONTACT_OPS),
                },
                # ── create / update — common fields ────────────────────
                {
                    "name": "given_name",
                    "label": "First name",
                    "type": "string",
                    "placeholder": "Alice",
                    "condition": _cond_any(*_CREATE_UPDATE_OPS),
                },
                {
                    "name": "family_name",
                    "label": "Last name",
                    "type": "string",
                    "placeholder": "Smith",
                    "condition": _cond_any(*_CREATE_UPDATE_OPS),
                },
                {
                    "name": "emails",
                    "label": "Emails",
                    "type": "json",
                    "placeholder": '["alice@example.com"]  or  [{"value":"alice@example.com","type":"work"}]',
                    "description": "Array of email strings or `{value, type}` dicts.",
                    "condition": _cond_any(*_CREATE_UPDATE_OPS),
                },
                {
                    "name": "phones",
                    "label": "Phones",
                    "type": "json",
                    "placeholder": '["+15551234567"]  or  [{"value":"+15551234567","type":"mobile"}]',
                    "condition": _cond_any(*_CREATE_UPDATE_OPS),
                },
                {
                    "name": "addresses",
                    "label": "Addresses",
                    "type": "json",
                    "placeholder": '[{"streetAddress":"1 Main St","city":"Boston","region":"MA","postalCode":"02110","country":"USA","type":"home"}]',
                    "description": "Array of address dicts (`streetAddress`, `city`, `region`, `postalCode`, `country`, `type`) or plain formatted strings.",
                    "condition": _cond_any(*_CREATE_UPDATE_OPS),
                    "mode": "advanced",
                },
                {
                    "name": "organization_name",
                    "label": "Organisation",
                    "type": "string",
                    "placeholder": "Acme Inc.",
                    "condition": _cond_any(*_CREATE_UPDATE_OPS),
                    "mode": "advanced",
                },
                {
                    "name": "organization_title",
                    "label": "Job title",
                    "type": "string",
                    "placeholder": "Engineer",
                    "condition": _cond_any(*_CREATE_UPDATE_OPS),
                    "mode": "advanced",
                },
                {
                    "name": "biography",
                    "label": "Biography / notes",
                    "type": "string",
                    "typeOptions": {"multiline": True, "rows": 3},
                    "condition": _cond_any(*_CREATE_UPDATE_OPS),
                    "mode": "advanced",
                },
                {
                    "name": "birthday",
                    "label": "Birthday",
                    "type": "datetime",
                    "typeOptions": {"granularity": "date"},
                    "condition": _cond_any(*_CREATE_UPDATE_OPS),
                    "mode": "advanced",
                },
                {
                    "name": "urls",
                    "label": "URLs",
                    "type": "json",
                    "placeholder": '["https://example.com", "https://github.com/alice"]',
                    "condition": _cond_any(*_CREATE_UPDATE_OPS),
                    "mode": "advanced",
                },
                # ── list_contacts ──────────────────────────────────────
                {
                    "name": "sort_order",
                    "label": "Sort order",
                    "type": "options",
                    "default": "LAST_MODIFIED_DESCENDING",
                    "options": [
                        {"label": "Last modified (newest)", "value": "LAST_MODIFIED_DESCENDING"},
                        {"label": "Last modified (oldest)", "value": "LAST_MODIFIED_ASCENDING"},
                        {"label": "First name (A → Z)", "value": "FIRST_NAME_ASCENDING"},
                        {"label": "Last name (A → Z)", "value": "LAST_NAME_ASCENDING"},
                    ],
                    "condition": _cond("list_contacts"),
                },
                {
                    "name": "page_size",
                    "label": "Page size",
                    "type": "number",
                    "default": 100,
                    "condition": _cond_any(
                        "list_contacts", "search_contacts", "list_other_contacts"
                    ),
                    "mode": "advanced",
                },
                {
                    "name": "page_token",
                    "label": "Page token",
                    "type": "string",
                    "placeholder": "Continuation token from prior call",
                    "condition": _cond_any("list_contacts", "list_other_contacts"),
                    "mode": "advanced",
                },
                {
                    "name": "person_fields",
                    "label": "Fields mask",
                    "type": "string",
                    "default": DEFAULT_PERSON_FIELDS,
                    "description": "Comma-separated People-API `personFields`. Default covers names, emails, phones, etc.",
                    "condition": _cond_any(
                        "list_contacts", "search_contacts", "get_contact", "list_other_contacts"
                    ),
                    "mode": "advanced",
                },
                # ── search_contacts ────────────────────────────────────
                {
                    "name": "query",
                    "label": "Search query",
                    "type": "string",
                    "required": True,
                    "placeholder": "alice@example.com  or  Smith",
                    "description": "Matches name, email, or phone substrings.",
                    "condition": _cond("search_contacts"),
                },
                # ── groups ─────────────────────────────────────────────
                {
                    "name": "group_resource_name",
                    "label": "Group",
                    "type": "gpeople-group",
                    "required": True,
                    "condition": _cond_any("delete_group", "add_to_group", "remove_from_group"),
                },
                {
                    "name": "group_name",
                    "label": "Group name",
                    "type": "string",
                    "required": True,
                    "placeholder": "VIP",
                    "condition": _cond("create_group"),
                },
                {
                    "name": "contact_resource_names",
                    "label": "Contact IDs",
                    "type": "json",
                    "required": True,
                    "placeholder": '["people/c123", "people/c456"]',
                    "description": "Array of contact resource names to add or remove.",
                    "condition": _cond_any("add_to_group", "remove_from_group"),
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "resource_name", "type": "string"},
                {"label": "display_name", "type": "string"},
                {"label": "emails", "type": "array"},
                {"label": "phones", "type": "array"},
            ],
            allow_error=True,
            credential_type="google_oauth",
        )

    def _get_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="Google OAuth credential required.")
        op = self.props.operation
        handler = _HANDLERS.get(op)
        if handler is None:
            return NodeResult(success=False, error=f"Unknown operation: {op}")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                return await handler(self, client, headers)
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=f"People API error {exc.response.status_code}: {exc.response.text[:300]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GooglePeopleNode {op} failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))


# ── payload builders ────────────────────────────────────────────────────


def _normalise_entries(raw: Any, value_field: str = "value") -> list[dict[str, Any]]:
    """Map ['x@y.com'] / [{'value': 'x@y.com', 'type': 'work'}] → People
    API array of `{value, type?}` dicts.

    Bare strings get wrapped to `{value: …}`; dicts pass through. Empty
    / non-list input returns []."""
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for entry in raw:
        if isinstance(entry, str):
            v = entry.strip()
            if v:
                out.append({value_field: v})
        elif isinstance(entry, dict):
            if entry.get(value_field):
                out.append(entry)
    return out


def _normalise_addresses(raw: Any) -> list[dict[str, Any]]:
    """Addresses can come as either formatted strings or structured
    dicts. We pass dicts through and wrap strings into `{formattedValue}`
    so the API parses them."""
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for entry in raw:
        if isinstance(entry, str) and entry.strip():
            out.append({"formattedValue": entry.strip()})
        elif isinstance(entry, dict) and any(
            entry.get(k) for k in ("streetAddress", "city", "formattedValue")
        ):
            out.append(entry)
    return out


def _normalise_urls(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    return [{"value": str(u)} for u in raw if str(u).strip()]


def _birthday_to_struct(value: str | None) -> dict[str, Any] | None:
    """`YYYY-MM-DD` → People API Date struct. Returns None on invalid
    input; the caller can decide whether to drop or error."""
    if not value:
        return None
    parts = value.strip().split("-")
    if len(parts) != 3:
        return None
    try:
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None
    return {"date": {"year": year, "month": month, "day": day}}


def _build_person_body(node: GooglePeopleNode) -> tuple[dict[str, Any], list[str]]:
    """Shape a `Person` payload + return the field mask we should send.
    Only fields the user actually set show up in the mask, so an
    `update_contact` call leaves untouched fields alone."""
    body: dict[str, Any] = {}
    mask: list[str] = []

    given = (node.props.given_name or "").strip()
    family = (node.props.family_name or "").strip()
    if given or family:
        body["names"] = [{"givenName": given, "familyName": family}]
        mask.append("names")

    emails = _normalise_entries(node.props.emails)
    if emails:
        body["emailAddresses"] = emails
        mask.append("emailAddresses")

    phones = _normalise_entries(node.props.phones)
    if phones:
        body["phoneNumbers"] = phones
        mask.append("phoneNumbers")

    addresses = _normalise_addresses(node.props.addresses)
    if addresses:
        body["addresses"] = addresses
        mask.append("addresses")

    org_name = (node.props.organization_name or "").strip()
    org_title = (node.props.organization_title or "").strip()
    if org_name or org_title:
        body["organizations"] = [{"name": org_name, "title": org_title}]
        mask.append("organizations")

    bio_raw = node.props.biography
    if bio_raw is not None and str(bio_raw).strip():
        body["biographies"] = [{"value": str(bio_raw), "contentType": "TEXT_PLAIN"}]
        mask.append("biographies")

    bday = _birthday_to_struct(node.props.birthday)
    if bday:
        body["birthdays"] = [bday]
        mask.append("birthdays")

    urls = _normalise_urls(node.props.urls)
    if urls:
        body["urls"] = urls
        mask.append("urls")

    return body, mask


# ── output flattening ───────────────────────────────────────────────────


def _flatten_contact(person: dict[str, Any]) -> dict[str, Any]:
    """Person resource → friendly flat dict for downstream nodes."""
    names = person.get("names") or []
    primary_name = names[0] if names else {}
    emails = person.get("emailAddresses") or []
    phones = person.get("phoneNumbers") or []
    orgs = person.get("organizations") or []
    primary_org = orgs[0] if orgs else {}
    return {
        "resource_name": person.get("resourceName"),
        "display_name": primary_name.get("displayName") or "",
        "given_name": primary_name.get("givenName") or "",
        "family_name": primary_name.get("familyName") or "",
        "emails": [e.get("value") for e in emails if e.get("value")],
        "phones": [p.get("value") for p in phones if p.get("value")],
        "organization": primary_org.get("name") or "",
        "title": primary_org.get("title") or "",
        "etag": person.get("etag") or "",
        "payload": person,
    }


# ── handlers ────────────────────────────────────────────────────────────


async def _list_contacts(
    node: GooglePeopleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    params = {
        "personFields": node.props.person_fields or DEFAULT_PERSON_FIELDS,
        "sortOrder": node.props.sort_order or "LAST_MODIFIED_DESCENDING",
        "pageSize": max(1, min(int(node.props.page_size or 100), 1000)),
    }
    if node.props.page_token:
        params["pageToken"] = node.props.page_token
    r = await client.get(f"{PEOPLE_API}/people/me/connections", headers=headers, params=params)
    r.raise_for_status()
    data = r.json()
    contacts = [_flatten_contact(p) for p in (data.get("connections") or [])]
    return NodeResult(
        success=True,
        output_data={
            "contacts": contacts,
            "next_page_token": data.get("nextPageToken"),
            "total_items": data.get("totalItems"),
        },
    )


async def _search_contacts(
    node: GooglePeopleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    query = (node.props.query or "").strip()
    if not query:
        return NodeResult(success=False, error="`query` is required.")
    # Warm the search index — first call may return empty until Google
    # indexes the query. Most production flows call once and accept this.
    r = await client.get(
        f"{PEOPLE_API}/people:searchContacts",
        headers=headers,
        params={
            "query": query,
            "readMask": node.props.person_fields or DEFAULT_PERSON_FIELDS,
            "pageSize": max(1, min(int(node.props.page_size or 30), 30)),
        },
    )
    r.raise_for_status()
    data = r.json()
    results = data.get("results") or []
    contacts = [_flatten_contact(r.get("person") or {}) for r in results]
    return NodeResult(success=True, output_data={"contacts": contacts})


async def _get_contact(
    node: GooglePeopleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    rn = (node.props.resource_name or "").strip()
    if not rn:
        return NodeResult(success=False, error="Contact ID is required.")
    r = await client.get(
        f"{PEOPLE_API}/{rn}",
        headers=headers,
        params={"personFields": node.props.person_fields or DEFAULT_PERSON_FIELDS},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=_flatten_contact(r.json()))


async def _create_contact(
    node: GooglePeopleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    body, mask = _build_person_body(node)
    if not mask:
        return NodeResult(success=False, error="Provide at least a name, email, or phone.")
    r = await client.post(
        f"{PEOPLE_API}/people:createContact",
        headers=headers,
        json=body,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=_flatten_contact(r.json()))


async def _update_contact(
    node: GooglePeopleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    rn = (node.props.resource_name or "").strip()
    if not rn:
        return NodeResult(success=False, error="Contact ID is required.")
    body, mask = _build_person_body(node)
    if not mask:
        return NodeResult(success=False, error="Pick at least one field to update.")
    # People API needs the contact's current etag to detect concurrent
    # edits. Fetch it now so user doesn't have to thread it through.
    head = await client.get(
        f"{PEOPLE_API}/{rn}",
        headers=headers,
        params={"personFields": "metadata"},
    )
    head.raise_for_status()
    body["etag"] = head.json().get("etag")
    r = await client.patch(
        f"{PEOPLE_API}/{rn}:updateContact",
        headers=headers,
        json=body,
        params={"updatePersonFields": ",".join(mask)},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=_flatten_contact(r.json()))


async def _delete_contact(
    node: GooglePeopleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    rn = (node.props.resource_name or "").strip()
    if not rn:
        return NodeResult(success=False, error="Contact ID is required.")
    r = await client.delete(f"{PEOPLE_API}/{rn}:deleteContact", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data={"resource_name": rn, "deleted": True})


async def _list_other_contacts(
    node: GooglePeopleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    """Other contacts = auto-saved interactions (people you've emailed
    but never explicitly saved). Useful for CRM-style enrichment."""
    params: dict[str, Any] = {
        "readMask": "names,emailAddresses,phoneNumbers,metadata",
        "pageSize": max(1, min(int(node.props.page_size or 100), 1000)),
    }
    if node.props.page_token:
        params["pageToken"] = node.props.page_token
    r = await client.get(f"{PEOPLE_API}/otherContacts", headers=headers, params=params)
    r.raise_for_status()
    data = r.json()
    contacts = [_flatten_contact(p) for p in (data.get("otherContacts") or [])]
    return NodeResult(
        success=True,
        output_data={
            "contacts": contacts,
            "next_page_token": data.get("nextPageToken"),
        },
    )


async def _list_groups(
    node: GooglePeopleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    r = await client.get(
        f"{PEOPLE_API}/contactGroups",
        headers=headers,
        params={"pageSize": 200, "groupFields": "name,memberCount,groupType"},
    )
    r.raise_for_status()
    data = r.json()
    groups = [
        {
            "resource_name": g.get("resourceName"),
            "name": g.get("name") or g.get("formattedName"),
            "member_count": g.get("memberCount") or 0,
            "type": g.get("groupType") or "",
        }
        for g in (data.get("contactGroups") or [])
    ]
    return NodeResult(success=True, output_data={"groups": groups})


async def _create_group(
    node: GooglePeopleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    name = (node.props.group_name or "").strip()
    if not name:
        return NodeResult(success=False, error="`group_name` is required.")
    r = await client.post(
        f"{PEOPLE_API}/contactGroups",
        headers=headers,
        json={"contactGroup": {"name": name}},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _delete_group(
    node: GooglePeopleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    rn = (node.props.group_resource_name or "").strip()
    if not rn:
        return NodeResult(success=False, error="Group is required.")
    r = await client.delete(
        f"{PEOPLE_API}/{rn}",
        headers=headers,
        params={"deleteContacts": "false"},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data={"resource_name": rn, "deleted": True})


def _require_member_list(node: GooglePeopleNode) -> list[str] | NodeResult:
    raw = node.props.contact_resource_names
    if not isinstance(raw, list) or not raw:
        return NodeResult(
            success=False,
            error="`contact_resource_names` must be a non-empty array.",
        )
    out = [str(r).strip() for r in raw if str(r).strip()]
    if not out:
        return NodeResult(success=False, error="`contact_resource_names` had no non-blank entries.")
    return out


async def _add_to_group(
    node: GooglePeopleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    rn = (node.props.group_resource_name or "").strip()
    if not rn:
        return NodeResult(success=False, error="Group is required.")
    members = _require_member_list(node)
    if isinstance(members, NodeResult):
        return members
    r = await client.post(
        f"{PEOPLE_API}/{rn}/members:modify",
        headers=headers,
        json={"resourceNamesToAdd": members},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _remove_from_group(
    node: GooglePeopleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    rn = (node.props.group_resource_name or "").strip()
    if not rn:
        return NodeResult(success=False, error="Group is required.")
    members = _require_member_list(node)
    if isinstance(members, NodeResult):
        return members
    r = await client.post(
        f"{PEOPLE_API}/{rn}/members:modify",
        headers=headers,
        json={"resourceNamesToRemove": members},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


_HANDLERS: dict[str, Any] = {
    "list_contacts": _list_contacts,
    "search_contacts": _search_contacts,
    "get_contact": _get_contact,
    "create_contact": _create_contact,
    "update_contact": _update_contact,
    "delete_contact": _delete_contact,
    "list_other_contacts": _list_other_contacts,
    "list_groups": _list_groups,
    "create_group": _create_group,
    "delete_group": _delete_group,
    "add_to_group": _add_to_group,
    "remove_from_group": _remove_from_group,
}
