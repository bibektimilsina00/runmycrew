"""Dropbox action node — manifest form.

Dropbox v2 API at `https://api.dropboxapi.com/2`. Bearer auth. Every
op is a POST with a JSON body (Dropbox's convention — no GETs for
resource listings).

The `path` field carries the Dropbox path (`/Documents/notes.txt`);
IDs are also supported (`id:abc123`).
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)

MANIFEST = ProviderManifest(
    type="action.dropbox",
    name="Dropbox",
    category="integration",
    description="Dropbox — files, folders, share links.",
    icon_slug="dropbox",
    color="#ffffff",
    base_url="https://api.dropboxapi.com/2",
    credential_type="dropbox_oauth",
    token_field=["access_token"],
    auth="bearer",
    fields=[
        FieldSpec(
            name="path",
            label="Folder",
            type="string",
            placeholder="/Documents/notes.txt",
            remote=RemoteLookup(provider="dropbox", resource="folders"),
        ),
        FieldSpec(name="from_path", label="From Path", type="string"),
        FieldSpec(name="to_path", label="To Path", type="string"),
        FieldSpec(name="content", label="Content", type="string"),
        FieldSpec(name="query", label="Search Query", type="string"),
        FieldSpec(
            name="autorename",
            label="Auto-rename on conflict",
            type="boolean",
            default=False,
            mode="advanced",
        ),
        FieldSpec(
            name="mute", label="Mute notifications", type="boolean", default=False, mode="advanced"
        ),
        FieldSpec(
            name="recursive",
            label="Recursive (list_folder)",
            type="boolean",
            default=False,
            mode="advanced",
        ),
        FieldSpec(name="limit", label="Limit", type="number", default=100, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_folder",
            label="List Folder",
            method="POST",
            path="/files/list_folder",
            visible_fields=["path", "recursive", "limit"],
            body_builder=lambda v: {
                "path": getattr(v, "path", None) or "",
                "recursive": bool(getattr(v, "recursive", False)),
                "limit": int(getattr(v, "limit", 100) or 100),
            },
        ),
        OpSpec(
            id="get_metadata",
            label="Get Metadata",
            method="POST",
            path="/files/get_metadata",
            visible_fields=["path"],
            body_builder=lambda v: {"path": getattr(v, "path", None) or ""},
        ),
        OpSpec(
            id="create_folder",
            label="Create Folder",
            method="POST",
            path="/files/create_folder_v2",
            visible_fields=["path", "autorename"],
            body_builder=lambda v: {
                "path": getattr(v, "path", None) or "",
                "autorename": bool(getattr(v, "autorename", False)),
            },
        ),
        OpSpec(
            id="delete",
            label="Delete",
            method="POST",
            path="/files/delete_v2",
            visible_fields=["path"],
            body_builder=lambda v: {"path": getattr(v, "path", None) or ""},
            success_payload_template={"deleted": True, "path": "{path}"},
        ),
        OpSpec(
            id="move",
            label="Move",
            method="POST",
            path="/files/move_v2",
            visible_fields=["from_path", "to_path", "autorename"],
            body_builder=lambda v: {
                "from_path": getattr(v, "from_path", None) or "",
                "to_path": getattr(v, "to_path", None) or "",
                "autorename": bool(getattr(v, "autorename", False)),
            },
        ),
        OpSpec(
            id="copy",
            label="Copy",
            method="POST",
            path="/files/copy_v2",
            visible_fields=["from_path", "to_path", "autorename"],
            body_builder=lambda v: {
                "from_path": getattr(v, "from_path", None) or "",
                "to_path": getattr(v, "to_path", None) or "",
                "autorename": bool(getattr(v, "autorename", False)),
            },
        ),
        OpSpec(
            id="search",
            label="Search",
            method="POST",
            path="/files/search_v2",
            visible_fields=["query", "limit"],
            body_builder=lambda v: {
                "query": getattr(v, "query", None) or "",
                "options": {"max_results": int(getattr(v, "limit", 100) or 100)},
            },
        ),
        OpSpec(
            id="create_share_link",
            label="Create Share Link",
            method="POST",
            path="/sharing/create_shared_link_with_settings",
            visible_fields=["path"],
            body_builder=lambda v: {"path": getattr(v, "path", None) or ""},
        ),
        OpSpec(
            id="get_current_account",
            label="Get Current Account",
            method="POST",
            path="/users/get_current_account",
            body_builder=lambda v: None,
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "path_display", "type": "string"},
        {"label": "entries", "type": "array"},
        {"label": "matches", "type": "array"},
        {"label": "url", "type": "string"},
    ],
    allow_error=True,
)
