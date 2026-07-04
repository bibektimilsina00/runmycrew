"""Outlook Mail polling trigger — manifest form.

Watches Microsoft Graph `/me/messages` for new mail. Since_timestamp
diff on `receivedDateTime` — Graph OData sorts by the same field so
newest lands first and cursor filters on `>= last-seen`.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)


def _flatten_message(item):
    frm = (item.get("from") or {}).get("emailAddress") or {}
    return {
        "id": item.get("id"),
        "subject": item.get("subject"),
        "from_name": frm.get("name"),
        "from_email": frm.get("address"),
        "receivedDateTime": item.get("receivedDateTime"),
        "isRead": item.get("isRead"),
        "hasAttachments": item.get("hasAttachments"),
        "bodyPreview": item.get("bodyPreview"),
        "webLink": item.get("webLink"),
        "conversationId": item.get("conversationId"),
    }


register_flatten("outlook.message", _flatten_message)


MANIFEST = PollingTriggerManifest(
    type="trigger.outlook_mail",
    name="Outlook Mail",
    description="Poll Outlook for new mail via Microsoft Graph.",
    icon_slug="outlook",
    color="#1c1c1c",
    base_url="https://graph.microsoft.com/v1.0",
    credential_type="microsoft_oauth",
    token_field=["access_token"],
    auth="bearer",
    provider="outlook_mail",
    default_poll_interval_seconds=60,
    common_fields=[
        FieldSpec(
            name="folder_id",
            label="Folder ID (optional; blank = Inbox)",
            type="string",
            mode="advanced",
        ),
        FieldSpec(
            name="top",
            label="Max results per poll",
            type="number",
            default=25,
            mode="advanced",
        ),
    ],
    events=[
        PollingEvent(
            id="new_mail",
            label="New Mail",
            list_path="/me/mailFolders/Inbox/messages",
            list_params={
                "$orderby": "receivedDateTime desc",
                "$top": "{top}",
                "$select": "id,subject,from,receivedDateTime,isRead,hasAttachments,bodyPreview,webLink,conversationId",
            },
            strategy="since_timestamp",
            timestamp_field="receivedDateTime",
            id_field="id",
            flatten="outlook.message",
        ),
        PollingEvent(
            id="new_flagged",
            label="New Flagged Mail",
            list_path="/me/messages",
            list_params={
                "$filter": "flag/flagStatus eq 'flagged'",
                "$orderby": "receivedDateTime desc",
                "$top": "{top}",
            },
            strategy="known_ids",
            id_field="id",
            flatten="outlook.message",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "subject", "type": "string"},
        {"label": "from_email", "type": "string"},
        {"label": "receivedDateTime", "type": "string"},
        {"label": "bodyPreview", "type": "string"},
    ],
)
