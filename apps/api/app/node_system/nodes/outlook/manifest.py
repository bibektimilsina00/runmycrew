"""Outlook action node — manifest form.

Microsoft Graph endpoints at `/v1.0/me/messages` and `/v1.0/me/mailFolders`.
Bearer auth via the shared microsoft_oauth credential. Seven ops cover
the typical Outlook workflow: list / get / send / reply / delete /
move messages + list folders.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)


def _odata_query(props):
    """Translate prop names to Microsoft Graph's $-prefixed query keys."""
    return {
        k: v
        for k, v in {
            "$filter": getattr(props, "filter", None),
            "$search": getattr(props, "search", None),
            "$top": int(getattr(props, "limit", 25) or 25),
            "$orderby": getattr(props, "orderby", None),
        }.items()
        if v not in (None, "")
    }


MANIFEST = ProviderManifest(
    type="action.outlook",
    name="Outlook",
    category="integration",
    description="Outlook mail — list, get, send, reply, move, delete messages.",
    icon_slug="outlook",
    color="#ffffff",
    base_url="https://graph.microsoft.com/v1.0",
    credential_type="microsoft_oauth",
    token_field=["access_token"],
    auth="bearer",
    fields=[
        FieldSpec(name="message_id", label="Message ID", type="string"),
        FieldSpec(name="folder_id", label="Folder ID", type="string", placeholder="inbox"),
        FieldSpec(name="to", label="To (CSV emails)", type="string"),
        FieldSpec(name="cc", label="CC", type="string", mode="advanced"),
        FieldSpec(name="bcc", label="BCC", type="string", mode="advanced"),
        FieldSpec(name="subject", label="Subject", type="string"),
        FieldSpec(name="body", label="Body (HTML or text)", type="string"),
        FieldSpec(
            name="body_type",
            label="Body Type",
            type="options",
            default="HTML",
            mode="advanced",
            options=[{"label": "HTML", "value": "HTML"}, {"label": "Text", "value": "Text"}],
        ),
        FieldSpec(name="reply_body", label="Reply Body", type="string"),
        FieldSpec(name="filter", label="$filter", type="string", mode="advanced"),
        FieldSpec(name="search", label="$search", type="string", mode="advanced"),
        FieldSpec(name="orderby", label="$orderby", type="string", mode="advanced"),
        FieldSpec(name="limit", label="Limit", type="number", default=25, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_messages",
            label="List Messages",
            method="GET",
            path="/me/messages",
            visible_fields=["filter", "search", "orderby", "limit"],
            query_builder=_odata_query,
        ),
        OpSpec(
            id="list_folder_messages",
            label="List Messages in Folder",
            method="GET",
            path="/me/mailFolders/{folder_id}/messages",
            visible_fields=["folder_id", "filter", "limit"],
            query_builder=_odata_query,
        ),
        OpSpec(
            id="get_message",
            label="Get Message",
            method="GET",
            path="/me/messages/{message_id}",
            visible_fields=["message_id"],
        ),
        OpSpec(
            id="send_message",
            label="Send Message",
            method="POST",
            path="/me/sendMail",
            visible_fields=["to", "cc", "bcc", "subject", "body", "body_type"],
            body_builder=lambda v: {
                "message": {
                    "subject": getattr(v, "subject", None) or "",
                    "body": {
                        "contentType": getattr(v, "body_type", None) or "HTML",
                        "content": getattr(v, "body", None) or "",
                    },
                    "toRecipients": _addrs(getattr(v, "to", None)),
                    "ccRecipients": _addrs(getattr(v, "cc", None)),
                    "bccRecipients": _addrs(getattr(v, "bcc", None)),
                },
                "saveToSentItems": True,
            },
        ),
        OpSpec(
            id="reply_message",
            label="Reply to Message",
            method="POST",
            path="/me/messages/{message_id}/reply",
            visible_fields=["message_id", "reply_body"],
            body_builder=lambda v: {"comment": getattr(v, "reply_body", None) or ""},
        ),
        OpSpec(
            id="move_message",
            label="Move Message",
            method="POST",
            path="/me/messages/{message_id}/move",
            visible_fields=["message_id", "folder_id"],
            body_builder=lambda v: {"destinationId": getattr(v, "folder_id", None) or ""},
        ),
        OpSpec(
            id="delete_message",
            label="Delete Message",
            method="DELETE",
            path="/me/messages/{message_id}",
            visible_fields=["message_id"],
            success_payload_template={"deleted": True, "id": "{message_id}"},
        ),
        OpSpec(
            id="list_folders",
            label="List Folders",
            method="GET",
            path="/me/mailFolders",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "subject", "type": "string"},
        {"label": "from", "type": "object"},
        {"label": "toRecipients", "type": "array"},
        {"label": "bodyPreview", "type": "string"},
        {"label": "value", "type": "array"},
        {"label": "@odata.nextLink", "type": "string"},
    ],
    allow_error=True,
)


def _addrs(csv: str | None) -> list[dict]:
    """Project a CSV email list into Graph's recipient object shape."""
    if not csv:
        return []
    return [
        {"emailAddress": {"address": email.strip()}}
        for email in str(csv).split(",")
        if email.strip()
    ]
