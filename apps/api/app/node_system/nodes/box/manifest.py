"""Box action node — manifest form.

Box REST API at `https://api.box.com/2.0`. Bearer auth via
box_oauth credential. Folder + file CRUD + share link ops.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.box",
    name="Box",
    category="integration",
    description="Box — cloud file storage, folders, share links.",
    icon_slug="box",
    color="#ffffff",
    base_url="https://api.box.com/2.0",
    credential_type="box_oauth",
    token_field=["access_token"],
    auth="bearer",
    fields=[
        FieldSpec(name="folder_id", label="Folder ID", type="string", placeholder="0 (root)"),
        FieldSpec(name="file_id", label="File ID", type="string"),
        FieldSpec(name="name", label="Name", type="string"),
        FieldSpec(name="parent_id", label="Parent Folder ID", type="string", default="0"),
        FieldSpec(
            name="access",
            label="Share Access",
            type="options",
            default="open",
            mode="advanced",
            options=[
                {"label": "Open (anyone with link)", "value": "open"},
                {"label": "Company", "value": "company"},
                {"label": "Collaborators only", "value": "collaborators"},
            ],
        ),
        FieldSpec(name="search_query", label="Search Query", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=100, mode="advanced"),
        FieldSpec(name="offset", label="Offset", type="number", default=0, mode="advanced"),
    ],
    operations=[
        OpSpec(id="get_me", label="Get Current User", method="GET", path="/users/me"),
        OpSpec(
            id="list_folder",
            label="List Folder Items",
            method="GET",
            path="/folders/{folder_id}/items",
            visible_fields=["folder_id", "limit", "offset"],
            query_fields=["limit", "offset"],
        ),
        OpSpec(
            id="get_folder",
            label="Get Folder",
            method="GET",
            path="/folders/{folder_id}",
            visible_fields=["folder_id"],
        ),
        OpSpec(
            id="create_folder",
            label="Create Folder",
            method="POST",
            path="/folders",
            visible_fields=["name", "parent_id"],
            body_builder=lambda v: {
                "name": getattr(v, "name", None) or "",
                "parent": {"id": getattr(v, "parent_id", None) or "0"},
            },
        ),
        OpSpec(
            id="delete_folder",
            label="Delete Folder",
            method="DELETE",
            path="/folders/{folder_id}",
            visible_fields=["folder_id"],
            success_payload_template={"deleted": True, "id": "{folder_id}"},
        ),
        OpSpec(
            id="get_file",
            label="Get File",
            method="GET",
            path="/files/{file_id}",
            visible_fields=["file_id"],
        ),
        OpSpec(
            id="rename_file",
            label="Rename File",
            method="PUT",
            path="/files/{file_id}",
            visible_fields=["file_id", "name"],
            body_builder=lambda v: {"name": getattr(v, "name", None) or ""},
        ),
        OpSpec(
            id="delete_file",
            label="Delete File",
            method="DELETE",
            path="/files/{file_id}",
            visible_fields=["file_id"],
            success_payload_template={"deleted": True, "id": "{file_id}"},
        ),
        OpSpec(
            id="create_share_link",
            label="Create Share Link",
            method="PUT",
            path="/files/{file_id}",
            visible_fields=["file_id", "access"],
            body_builder=lambda v: {
                "shared_link": {"access": getattr(v, "access", None) or "open"}
            },
        ),
        OpSpec(
            id="search",
            label="Search",
            method="GET",
            path="/search",
            visible_fields=["search_query", "limit"],
            query_builder=lambda v: {
                "query": getattr(v, "search_query", None) or "",
                "limit": int(getattr(v, "limit", 100) or 100),
            },
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "type", "type": "string"},
        {"label": "shared_link", "type": "object"},
        {"label": "entries", "type": "array"},
        {"label": "total_count", "type": "number"},
    ],
    allow_error=True,
)
