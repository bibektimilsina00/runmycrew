"""OneDrive action node — manifest form.

Graph endpoints at `/v1.0/me/drive/...` for personal OneDrive and
`/v1.0/drives/{drive_id}/...` for shared SharePoint drives.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.onedrive",
    name="OneDrive",
    category="integration",
    description="OneDrive — list, get, upload, download, move, delete files.",
    icon_slug="onedrive",
    color="#ffffff",
    base_url="https://graph.microsoft.com/v1.0",
    credential_type="microsoft_oauth",
    token_field=["access_token"],
    auth="bearer",
    fields=[
        FieldSpec(name="item_id", label="Item ID", type="string"),
        FieldSpec(name="folder_id", label="Folder ID", type="string", placeholder="root"),
        FieldSpec(
            name="path",
            label="Path",
            type="string",
            placeholder="Documents/notes.txt",
            mode="advanced",
        ),
        FieldSpec(name="filename", label="File Name", type="string"),
        FieldSpec(name="content", label="Content (text)", type="string"),
        FieldSpec(name="search_query", label="Search", type="string"),
        FieldSpec(name="new_parent_id", label="New Parent Folder ID", type="string"),
        FieldSpec(name="new_name", label="New Name", type="string", mode="advanced"),
        FieldSpec(name="limit", label="Limit", type="number", default=50, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_root",
            label="List Root Items",
            method="GET",
            path="/me/drive/root/children",
            visible_fields=["limit"],
            query_builder=lambda v: {"$top": int(getattr(v, "limit", 50) or 50)},
        ),
        OpSpec(
            id="list_folder",
            label="List Folder",
            method="GET",
            path="/me/drive/items/{folder_id}/children",
            visible_fields=["folder_id", "limit"],
            query_builder=lambda v: {"$top": int(getattr(v, "limit", 50) or 50)},
        ),
        OpSpec(
            id="get_item",
            label="Get Item",
            method="GET",
            path="/me/drive/items/{item_id}",
            visible_fields=["item_id"],
        ),
        OpSpec(
            id="upload_file",
            label="Upload Small File",
            method="PUT",
            path="/me/drive/items/{folder_id}:/{filename}:/content",
            visible_fields=["folder_id", "filename", "content"],
            body_builder=lambda v: getattr(v, "content", None) or "",
        ),
        OpSpec(
            id="download_file",
            label="Download File (content URL)",
            method="GET",
            path="/me/drive/items/{item_id}/content",
            visible_fields=["item_id"],
        ),
        OpSpec(
            id="search",
            label="Search",
            method="GET",
            path="/me/drive/root/search(q='{search_query}')",
            visible_fields=["search_query", "limit"],
            query_builder=lambda v: {"$top": int(getattr(v, "limit", 50) or 50)},
        ),
        OpSpec(
            id="move_item",
            label="Move Item",
            method="PATCH",
            path="/me/drive/items/{item_id}",
            visible_fields=["item_id", "new_parent_id", "new_name"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "parentReference": (
                        {"id": getattr(v, "new_parent_id", None)}
                        if getattr(v, "new_parent_id", None)
                        else None
                    ),
                    "name": getattr(v, "new_name", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="delete_item",
            label="Delete Item",
            method="DELETE",
            path="/me/drive/items/{item_id}",
            visible_fields=["item_id"],
            success_payload_template={"deleted": True, "id": "{item_id}"},
        ),
        OpSpec(
            id="create_folder",
            label="Create Folder",
            method="POST",
            path="/me/drive/items/{folder_id}/children",
            visible_fields=["folder_id", "filename"],
            body_builder=lambda v: {
                "name": getattr(v, "filename", None) or "New Folder",
                "folder": {},
                "@microsoft.graph.conflictBehavior": "rename",
            },
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "size", "type": "number"},
        {"label": "webUrl", "type": "string"},
        {"label": "value", "type": "array"},
        {"label": "@odata.nextLink", "type": "string"},
    ],
    allow_error=True,
)
