"""Attio action node — manifest form.

Attio is a flexible-schema CRM exposing a Records-style API at
`https://api.attio.com/v2`. Bearer auth. Records belong to *objects*
(people, companies, deals, …), so every record op takes an
`object_slug` path segment.
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.attio import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.attio",
    name=NAME,
    category="integration",
    description="Attio CRM — manage records on any custom object schema.",
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://api.attio.com/v2",
    credential_type="attio_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(
            name="object_slug",
            label="Object",
            type="string",
            placeholder="people | companies | deals | custom_slug",
        ),
        FieldSpec(name="record_id", label="Record ID", type="string"),
        FieldSpec(name="data", label="Record values (JSON)", type="json"),
        FieldSpec(name="filter", label="Filter (JSON)", type="json", mode="advanced"),
        FieldSpec(name="sorts", label="Sorts (JSON)", type="json", mode="advanced"),
        FieldSpec(name="limit", label="Limit", type="number", default=25, mode="advanced"),
        FieldSpec(name="offset", label="Offset", type="number", default=0, mode="advanced"),
        FieldSpec(name="list_id", label="List ID", type="string"),
        FieldSpec(name="entry_data", label="Entry values (JSON)", type="json"),
        FieldSpec(name="entry_id", label="List Entry ID", type="string"),
        FieldSpec(name="note_id", label="Note ID", type="string"),
        FieldSpec(name="title", label="Title", type="string"),
        FieldSpec(name="content", label="Content (Markdown)", type="string"),
        FieldSpec(name="parent_object", label="Parent Object", type="string"),
        FieldSpec(name="parent_record_id", label="Parent Record ID", type="string"),
        FieldSpec(name="task_id", label="Task ID", type="string"),
        FieldSpec(name="assignees", label="Assignees (JSON array)", type="json", default=[]),
        FieldSpec(name="deadline_at", label="Deadline (ISO)", type="string"),
        FieldSpec(name="is_completed", label="Is Completed", type="boolean", default=False),
        FieldSpec(name="linked_records", label="Linked Records (JSON)", type="json", default=[]),
        FieldSpec(name="thread_id", label="Thread ID", type="string"),
        FieldSpec(name="comment_id", label="Comment ID", type="string"),
        FieldSpec(name="member_id", label="Workspace Member ID", type="string"),
        FieldSpec(name="webhook_id", label="Webhook ID", type="string"),
        FieldSpec(name="webhook_url", label="Webhook URL", type="string"),
        FieldSpec(
            name="webhook_subscriptions", label="Subscriptions (JSON)", type="json", default=[]
        ),
    ],
    operations=[
        OpSpec(
            id="create_record",
            label="Create Record",
            method="POST",
            path="/objects/{object_slug}/records",
            visible_fields=["object_slug", "data"],
            body_builder=lambda v: {"data": {"values": getattr(v, "data", None) or {}}},
        ),
        OpSpec(
            id="get_record",
            label="Get Record",
            method="GET",
            path="/objects/{object_slug}/records/{record_id}",
            visible_fields=["object_slug", "record_id"],
        ),
        OpSpec(
            id="update_record",
            label="Update Record",
            method="PATCH",
            path="/objects/{object_slug}/records/{record_id}",
            visible_fields=["object_slug", "record_id", "data"],
            body_builder=lambda v: {"data": {"values": getattr(v, "data", None) or {}}},
        ),
        OpSpec(
            id="delete_record",
            label="Delete Record",
            method="DELETE",
            path="/objects/{object_slug}/records/{record_id}",
            visible_fields=["object_slug", "record_id"],
            success_payload_template={"deleted": True, "id": "{record_id}"},
        ),
        OpSpec(
            id="list_records",
            label="Query Records",
            method="POST",
            path="/objects/{object_slug}/records/query",
            visible_fields=["object_slug", "filter", "sorts", "limit", "offset"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "filter": getattr(v, "filter", None),
                    "sorts": getattr(v, "sorts", None),
                    "limit": int(getattr(v, "limit", 25) or 25),
                    "offset": int(getattr(v, "offset", 0) or 0),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="list_objects",
            label="List Objects",
            method="GET",
            path="/objects",
        ),
        OpSpec(
            id="get_object",
            label="Get Object",
            method="GET",
            path="/objects/{object_slug}",
            visible_fields=["object_slug"],
        ),
        OpSpec(
            id="assert_record",
            label="Assert Record (upsert by matching_attribute)",
            method="PUT",
            path="/objects/{object_slug}/records",
            visible_fields=["object_slug", "data"],
            body_builder=lambda v: {"data": {"values": getattr(v, "data", None) or {}}},
        ),
        OpSpec(
            id="list_lists",
            label="List Lists",
            method="GET",
            path="/lists",
        ),
        OpSpec(
            id="get_list",
            label="Get List",
            method="GET",
            path="/lists/{list_id}",
            visible_fields=["list_id"],
        ),
        OpSpec(
            id="create_list",
            label="Create List",
            method="POST",
            path="/lists",
            visible_fields=["title", "parent_object"],
            body_builder=lambda v: {
                "data": {
                    "name": getattr(v, "title", "") or "",
                    "parent_object": getattr(v, "parent_object", "") or "",
                }
            },
        ),
        OpSpec(
            id="update_list",
            label="Update List",
            method="PATCH",
            path="/lists/{list_id}",
            visible_fields=["list_id", "title"],
            body_builder=lambda v: {"data": {"name": getattr(v, "title", "") or ""}},
        ),
        OpSpec(
            id="add_to_list",
            label="Add to List (Create Entry)",
            method="POST",
            path="/lists/{list_id}/entries",
            visible_fields=["list_id", "entry_data"],
            body_builder=lambda v: {"data": {"entry_values": getattr(v, "entry_data", None) or {}}},
        ),
        OpSpec(
            id="query_list_entries",
            label="Query List Entries",
            method="POST",
            path="/lists/{list_id}/entries/query",
            visible_fields=["list_id", "filter", "sorts", "limit", "offset"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "filter": getattr(v, "filter", None),
                    "sorts": getattr(v, "sorts", None),
                    "limit": int(getattr(v, "limit", 25) or 25),
                    "offset": int(getattr(v, "offset", 0) or 0),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_list_entry",
            label="Get List Entry",
            method="GET",
            path="/lists/{list_id}/entries/{entry_id}",
            visible_fields=["list_id", "entry_id"],
        ),
        OpSpec(
            id="update_list_entry",
            label="Update List Entry",
            method="PATCH",
            path="/lists/{list_id}/entries/{entry_id}",
            visible_fields=["list_id", "entry_id", "entry_data"],
            body_builder=lambda v: {"data": {"entry_values": getattr(v, "entry_data", None) or {}}},
        ),
        OpSpec(
            id="delete_list_entry",
            label="Delete List Entry",
            method="DELETE",
            path="/lists/{list_id}/entries/{entry_id}",
            visible_fields=["list_id", "entry_id"],
        ),
        OpSpec(
            id="list_notes",
            label="List Notes",
            method="GET",
            path="/notes",
            visible_fields=["parent_object", "parent_record_id", "limit"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "parent_object": getattr(v, "parent_object", None) or None,
                    "parent_record_id": getattr(v, "parent_record_id", None) or None,
                    "limit": int(getattr(v, "limit", 25) or 25),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_note",
            label="Get Note",
            method="GET",
            path="/notes/{note_id}",
            visible_fields=["note_id"],
        ),
        OpSpec(
            id="create_note",
            label="Create Note",
            method="POST",
            path="/notes",
            visible_fields=["parent_object", "parent_record_id", "title", "content"],
            body_builder=lambda v: {
                "data": {
                    "parent_object": getattr(v, "parent_object", "") or "",
                    "parent_record_id": getattr(v, "parent_record_id", "") or "",
                    "title": getattr(v, "title", "") or "",
                    "content": getattr(v, "content", "") or "",
                    "format": "markdown",
                }
            },
        ),
        OpSpec(
            id="delete_note",
            label="Delete Note",
            method="DELETE",
            path="/notes/{note_id}",
            visible_fields=["note_id"],
        ),
        OpSpec(
            id="list_tasks",
            label="List Tasks",
            method="GET",
            path="/tasks",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 25) or 25)},
        ),
        OpSpec(
            id="get_task",
            label="Get Task",
            method="GET",
            path="/tasks/{task_id}",
            visible_fields=["task_id"],
        ),
        OpSpec(
            id="create_task",
            label="Create Task",
            method="POST",
            path="/tasks",
            visible_fields=["content", "deadline_at", "assignees", "linked_records"],
            body_builder=lambda v: {
                "data": {
                    "content": getattr(v, "content", "") or "",
                    "format": "plaintext",
                    "deadline_at": getattr(v, "deadline_at", None) or None,
                    "assignees": getattr(v, "assignees", []) or [],
                    "linked_records": getattr(v, "linked_records", []) or [],
                    "is_completed": bool(getattr(v, "is_completed", False)),
                }
            },
        ),
        OpSpec(
            id="update_task",
            label="Update Task",
            method="PATCH",
            path="/tasks/{task_id}",
            visible_fields=["task_id", "content", "is_completed", "deadline_at"],
            body_builder=lambda v: {
                "data": {
                    k: val
                    for k, val in {
                        "content": getattr(v, "content", None) or None,
                        "is_completed": bool(getattr(v, "is_completed", False)),
                        "deadline_at": getattr(v, "deadline_at", None) or None,
                    }.items()
                    if val is not None
                }
            },
        ),
        OpSpec(
            id="delete_task",
            label="Delete Task",
            method="DELETE",
            path="/tasks/{task_id}",
            visible_fields=["task_id"],
        ),
        OpSpec(
            id="list_members",
            label="List Workspace Members",
            method="GET",
            path="/workspace_members",
        ),
        OpSpec(
            id="get_member",
            label="Get Workspace Member",
            method="GET",
            path="/workspace_members/{member_id}",
            visible_fields=["member_id"],
        ),
        OpSpec(
            id="list_threads",
            label="List Threads",
            method="GET",
            path="/threads",
        ),
        OpSpec(
            id="get_thread",
            label="Get Thread",
            method="GET",
            path="/threads/{thread_id}",
            visible_fields=["thread_id"],
        ),
        OpSpec(
            id="create_comment",
            label="Create Comment",
            method="POST",
            path="/comments",
            visible_fields=["thread_id", "content"],
            body_builder=lambda v: {
                "data": {
                    "thread_id": getattr(v, "thread_id", "") or "",
                    "content_plaintext": getattr(v, "content", "") or "",
                }
            },
        ),
        OpSpec(
            id="get_comment",
            label="Get Comment",
            method="GET",
            path="/comments/{comment_id}",
            visible_fields=["comment_id"],
        ),
        OpSpec(
            id="delete_comment",
            label="Delete Comment",
            method="DELETE",
            path="/comments/{comment_id}",
            visible_fields=["comment_id"],
        ),
        OpSpec(
            id="list_webhooks",
            label="List Webhooks",
            method="GET",
            path="/webhooks",
        ),
        OpSpec(
            id="get_webhook",
            label="Get Webhook",
            method="GET",
            path="/webhooks/{webhook_id}",
            visible_fields=["webhook_id"],
        ),
        OpSpec(
            id="create_webhook",
            label="Create Webhook",
            method="POST",
            path="/webhooks",
            visible_fields=["webhook_url", "webhook_subscriptions"],
            body_builder=lambda v: {
                "data": {
                    "target_url": getattr(v, "webhook_url", "") or "",
                    "subscriptions": getattr(v, "webhook_subscriptions", []) or [],
                }
            },
        ),
        OpSpec(
            id="update_webhook",
            label="Update Webhook",
            method="PATCH",
            path="/webhooks/{webhook_id}",
            visible_fields=["webhook_id", "webhook_url", "webhook_subscriptions"],
            body_builder=lambda v: {
                "data": {
                    k: val
                    for k, val in {
                        "target_url": getattr(v, "webhook_url", None) or None,
                        "subscriptions": getattr(v, "webhook_subscriptions", None) or None,
                    }.items()
                    if val is not None
                }
            },
        ),
        OpSpec(
            id="delete_webhook",
            label="Delete Webhook",
            method="DELETE",
            path="/webhooks/{webhook_id}",
            visible_fields=["webhook_id"],
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "object"},
        {"label": "items", "type": "array"},
    ],
    allow_error=True,
)
