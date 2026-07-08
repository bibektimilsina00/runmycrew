"""Salesforce polling trigger — manifest form.

Salesforce REST v59 at `{instance_url}/services/data/v59.0`. Bearer
auth via a Connected App access token. Each customer's `instance_url`
is stored on the credential (`instance_url` field) — the paginate_fn
reads it since it can't live in a static `manifest.base_url`.

Events (poll-observable subset of sim's 5):
  - `record_created` — SOQL `SELECT ... FROM {object} ORDER BY
    CreatedDate DESC` — new records on any SObject.
  - `record_updated` — SOQL sorted by LastModifiedDate; since_timestamp
    diff on the field.
  - `opportunity_stage_changed` — poll opportunities with StageName +
    LastModifiedDate; custom-diff on StageName per opp id.

Not in polling — need Salesforce Platform Events or Streaming API:
  record_deleted, case_status_changed (fires on state transitions
  which the poll can only see indirectly via LastModifiedDate).
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.node_system.nodes.salesforce import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)
from apps.api.app.node_system.scaffolds.field_resolvers import resolve_template

SF_API_VERSION = "v59.0"


def _flatten_record(item):
    attrs = item.get("attributes") or {}
    out = {
        "id": item.get("Id"),
        "type": attrs.get("type"),
        "url": attrs.get("url"),
        "created_date": item.get("CreatedDate"),
        "last_modified_date": item.get("LastModifiedDate"),
        # Hoist common fields the workflow will want without a
        # field-by-field JSONata reach:
        "name": item.get("Name"),
        "subject": item.get("Subject"),
        "status": item.get("Status"),
        "stage": item.get("StageName"),
        "amount": item.get("Amount"),
        "owner_id": item.get("OwnerId"),
    }
    return out


register_flatten("salesforce.record", _flatten_record)


def _diff_stage_changed(items, cursor, props, event_id):
    """Custom diff — fire when an opportunity's StageName changed
    between polls. Cursor tracks `{opp_id: last_seen_stage}`; first
    poll snapshots silently."""
    object_slug = str(getattr(props, "object_type", "Opportunity") or "Opportunity")
    prior: dict[str, str] | None = None
    if (
        isinstance(cursor, dict)
        and cursor.get("event_type") == event_id
        and cursor.get("object_type") == object_slug
    ):
        prior = cursor.get("stages")
        if not isinstance(prior, dict):
            prior = None

    new_stages: dict[str, str] = {}
    matches: list[dict[str, Any]] = []
    first_poll = prior is None
    for item in items:
        opp_id = str(item.get("Id") or "")
        if not opp_id:
            continue
        stage = str(item.get("StageName") or "")
        new_stages[opp_id] = stage
        if first_poll:
            continue
        prev = prior.get(opp_id) if isinstance(prior, dict) else None
        if prev is not None and prev != stage:
            flat = _flatten_record(item)
            flat["event_type"] = event_id
            flat["change"] = {"key": "StageName", "from": prev, "to": stage}
            matches.append(flat)

    new_cursor: dict[str, Any] = {
        "event_type": event_id,
        "object_type": object_slug,
        "stages": new_stages,
    }
    return matches, new_cursor


async def _walk_salesforce(
    client: httpx.AsyncClient,
    *,
    manifest,
    event,
    token: str | None,
    props: Any,
) -> list[dict[str, Any]]:
    """Salesforce REST is instance-url scoped; each user's org has a
    different host. Read the instance_url from the credential, build
    the SOQL query, POST to `/services/data/v59.0/query`.
    """
    cred = getattr(props, "_cred", None) or {}
    instance_url = str(cred.get("instance_url") or "").rstrip("/")
    if not instance_url or not token:
        return []
    object_type = resolve_template("{object_type}", props) or "Account"
    limit_raw = getattr(props, "max_per_poll", 25) or 25
    try:
        limit = max(1, min(int(limit_raw), 200))
    except (TypeError, ValueError):
        limit = 25

    # Extra fields the user wants surfaced. Blank = default.
    default_fields = "Id, Name, CreatedDate, LastModifiedDate, OwnerId"
    if event.id == "opportunity_stage_changed":
        default_fields = "Id, Name, StageName, Amount, CreatedDate, LastModifiedDate, OwnerId"
    extra = str(getattr(props, "fields", "") or "").strip()
    fields = extra or default_fields

    order = "LastModifiedDate DESC" if event.id == "record_updated" else "CreatedDate DESC"
    soql = f"SELECT {fields} FROM {object_type} ORDER BY {order} LIMIT {limit}"

    url = f"{instance_url}/services/data/{SF_API_VERSION}/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    resp = await client.get(url, headers=headers, params={"q": soql}, timeout=30)
    resp.raise_for_status()
    payload = resp.json() or {}
    records = payload.get("records") or []
    # For record_updated: hoist LastModifiedDate → updated for the
    # scaffold's since_timestamp diff to key on.
    if event.id == "record_updated":
        for r in records:
            if r.get("LastModifiedDate"):
                r["updated"] = r["LastModifiedDate"]
    return records


MANIFEST = PollingTriggerManifest(
    type="trigger.salesforce",
    name=NAME,
    description=(
        "Poll Salesforce for new / updated records or opportunity stage "
        "changes on any SObject. Uses Connected App access token + "
        "instance URL from the credential."
    ),
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="",  # unused — paginate_fn reads instance_url per cred
    credential_type="salesforce_api_key",
    token_field=["api_key", "access_token"],
    auth="none",  # paginate_fn builds the Authorization header itself
    provider="salesforce",
    default_poll_interval_seconds=60,
    common_fields=[
        FieldSpec(
            name="object_type",
            label="SObject",
            type="string",
            default="Account",
            placeholder="Account | Contact | Lead | Opportunity | Case | ...",
        ),
        FieldSpec(
            name="fields",
            label="SOQL SELECT fields (comma-separated; blank = defaults)",
            type="string",
            mode="advanced",
            placeholder="Id, Name, Amount, StageName",
        ),
    ],
    events=[
        PollingEvent(
            id="record_created",
            label="Record Created",
            list_path="",
            strategy="known_ids",
            id_field="Id",
            flatten="salesforce.record",
        ),
        PollingEvent(
            id="record_updated",
            label="Record Updated",
            list_path="",
            strategy="since_timestamp",
            timestamp_field="updated",
            flatten="salesforce.record",
        ),
        PollingEvent(
            id="opportunity_stage_changed",
            label="Opportunity Stage Changed",
            list_path="",
            diff_handler=_diff_stage_changed,
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "type", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "stage", "type": "string"},
        {"label": "amount", "type": "number"},
        {"label": "created_date", "type": "string"},
        {"label": "last_modified_date", "type": "string"},
        {"label": "change", "type": "object"},
    ],
    paginate_fn=_walk_salesforce,
)
