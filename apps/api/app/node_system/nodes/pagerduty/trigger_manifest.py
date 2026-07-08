"""PagerDuty polling trigger — manifest form.

Watches incidents on a service (or account-wide). PagerDuty's REST
v2 API uses custom `Authorization: Token token={key}` — modeled via
`bearer` scheme with a custom value template.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)


def _flatten_incident(item):
    service = item.get("service") or {}
    return {
        "id": item.get("id"),
        "incident_number": item.get("incident_number"),
        "title": item.get("title"),
        "status": item.get("status"),
        "urgency": item.get("urgency"),
        "service_id": service.get("id"),
        "service_summary": service.get("summary"),
        "html_url": item.get("html_url"),
        "created_at": item.get("created_at"),
    }


register_flatten("pagerduty.incident", _flatten_incident)


MANIFEST = PollingTriggerManifest(
    type="trigger.pagerduty",
    name="PagerDuty",
    description="Poll PagerDuty for new incidents (all or scoped to a service).",
    icon_slug="pagerduty",
    color="#ffffff",
    base_url="https://api.pagerduty.com",
    credential_type="pagerduty_api_key",
    token_field=["api_key"],
    auth="bearer",
    auth_value_template="Token token={token}",
    extra_headers={"Accept": "application/vnd.pagerduty+json;version=2"},
    provider="pagerduty",
    default_poll_interval_seconds=60,
    common_fields=[
        FieldSpec(
            name="service_ids",
            label="Service IDs (CSV, optional)",
            type="string",
            placeholder="P123ABC,P456DEF",
            mode="advanced",
        ),
        FieldSpec(
            name="limit",
            label="Limit",
            type="number",
            default=25,
            mode="advanced",
        ),
    ],
    events=[
        PollingEvent(
            id="new_incident",
            label="New Incident",
            list_path="/incidents",
            list_params={
                "statuses[]": "triggered",
                "limit": "{limit}",
                "sort_by": "created_at:desc",
            },
            strategy="known_ids",
            id_field="id",
            flatten="pagerduty.incident",
        ),
        PollingEvent(
            id="acknowledged_incident",
            label="Acknowledged Incident",
            list_path="/incidents",
            list_params={
                "statuses[]": "acknowledged",
                "limit": "{limit}",
                "sort_by": "created_at:desc",
            },
            strategy="known_ids",
            id_field="id",
            flatten="pagerduty.incident",
        ),
        PollingEvent(
            id="resolved_incident",
            label="Resolved Incident",
            list_path="/incidents",
            list_params={
                "statuses[]": "resolved",
                "limit": "{limit}",
                "sort_by": "created_at:desc",
            },
            strategy="known_ids",
            id_field="id",
            flatten="pagerduty.incident",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "incident_number", "type": "number"},
        {"label": "title", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "urgency", "type": "string"},
        {"label": "service_summary", "type": "string"},
        {"label": "html_url", "type": "string"},
    ],
)
