"""Intercom polling trigger — manifest form.

Watches for new contacts and new conversations. Intercom's list
endpoints return `data: [...]` with `pages.next.starting_after` for
continuation — the scaffold's default list-under-`data` extraction
handles one page, which is all polling needs (newest at top).
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.intercom import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)


def _flatten_contact(item):
    return {
        "id": item.get("id"),
        "external_id": item.get("external_id"),
        "email": item.get("email"),
        "name": item.get("name"),
        "role": item.get("role"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
    }


def _flatten_conversation(item):
    source = item.get("source") or {}
    return {
        "id": item.get("id"),
        "state": item.get("state"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "source_type": source.get("type"),
        "source_subject": source.get("subject"),
        "author_email": (source.get("author") or {}).get("email"),
        "read": item.get("read"),
        "open": item.get("open"),
    }


register_flatten("intercom.contact", _flatten_contact)
register_flatten("intercom.conversation", _flatten_conversation)


MANIFEST = PollingTriggerManifest(
    type="trigger.intercom",
    name=NAME,
    description="Poll Intercom for new contacts or new conversations.",
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://api.intercom.io",
    credential_type="intercom_api_key",
    token_field=["api_key"],
    auth="bearer",
    extra_headers={"Intercom-Version": "2.13"},
    provider="intercom",
    default_poll_interval_seconds=60,
    common_fields=[
        FieldSpec(
            name="per_page",
            label="Per Page",
            type="number",
            default=25,
            mode="advanced",
        ),
    ],
    events=[
        PollingEvent(
            id="new_contact",
            label="New Contact",
            list_path="/contacts",
            list_params={
                "per_page": "{per_page}",
                "order": "desc",
                "sort": "created_at",
            },
            strategy="known_ids",
            id_field="id",
            flatten="intercom.contact",
        ),
        PollingEvent(
            id="updated_contact",
            label="Contact Updated",
            list_path="/contacts",
            list_params={
                "per_page": "{per_page}",
                "order": "desc",
                "sort": "updated_at",
            },
            strategy="since_timestamp",
            timestamp_field="updated_at",
            flatten="intercom.contact",
        ),
        PollingEvent(
            id="new_conversation",
            label="New Conversation",
            list_path="/conversations",
            list_params={
                "per_page": "{per_page}",
                "order": "desc",
                "sort": "created_at",
            },
            strategy="known_ids",
            id_field="id",
            flatten="intercom.conversation",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "email", "type": "string"},
        {"label": "state", "type": "string"},
        {"label": "created_at", "type": "number"},
        {"label": "updated_at", "type": "number"},
    ],
)
