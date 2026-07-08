"""Evernote action node — Evernote — notes, notebooks, tags.

REST at https://api.evernote.com. See sim-parity roadmap Phase 4.23.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.evernote",
    name="Evernote",
    category="integration",
    description="Evernote — notes, notebooks, tags.",
    icon_slug="evernote",
    color="#ffffff",
    base_url="https://api.evernote.com",
    credential_type="evernote_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="meeting_id", label="Meeting ID", type="string"),
        FieldSpec(name="note_id", label="Note ID", type="string"),
        FieldSpec(name="note_guid", label="Note GUID", type="string"),
        FieldSpec(name="notebook_guid", label="Notebook GUID", type="string"),
        FieldSpec(name="title", label="Title", type="string"),
        FieldSpec(name="content", label="Content", type="string"),
        FieldSpec(name="workflow_id", label="Workflow ID", type="string"),
        FieldSpec(name="run_id", label="Run ID", type="string"),
        FieldSpec(name="url", label="Document URL", type="string"),
        FieldSpec(name="calendar_api_id", label="Calendar API ID", type="string"),
        FieldSpec(name="api_id", label="Event API ID", type="string"),
        FieldSpec(name="guests", label="Guests (JSON array of {email, name})", type="json"),
        FieldSpec(name="limit", label="Limit", type="number", default=25, mode="advanced"),
        FieldSpec(name="en_note_guid", label="Note GUID", type="string"),
        FieldSpec(name="en_note_body", label="Note Body (JSON)", type="json", default={}),
        FieldSpec(name="en_search_query", label="Search Query", type="string"),
        FieldSpec(name="en_notebook_guid", label="Notebook GUID", type="string"),
        FieldSpec(name="en_notebook_body", label="Notebook Body (JSON)", type="json", default={}),
        FieldSpec(name="en_tag_name", label="Tag Name", type="string"),
    ],
    operations=[
        OpSpec(
            id="list_notes",
            label="List Notes",
            method="GET",
            path="/v1/notes",
            visible_fields=["notebook_guid", "limit"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "notebookGuid": getattr(v, "notebook_guid", None) or None,
                    "maxNotes": int(getattr(v, "limit", 25) or 25),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_note",
            label="Get Note",
            method="GET",
            path="/v1/notes/{note_guid}",
            visible_fields=["note_guid"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_note",
            label="Create Note",
            method="POST",
            path="/v1/notes",
            visible_fields=["title", "content", "notebook_guid"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "title": getattr(v, "title", None) or None,
                    "content": getattr(v, "content", None) or None,
                    "notebookGuid": getattr(v, "notebook_guid", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="list_notebooks",
            label="List Notebooks",
            method="GET",
            path="/v1/notebooks",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="update_note",
            label="Update Note",
            method="PUT",
            path="/notes/{en_note_guid}",
            visible_fields=["en_note_guid", "en_note_body"],
            body_builder=lambda v: getattr(v, "en_note_body", None) or {},
        ),
        OpSpec(
            id="delete_note",
            label="Delete Note",
            method="DELETE",
            path="/notes/{en_note_guid}",
            visible_fields=["en_note_guid"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="copy_note",
            label="Copy Note",
            method="POST",
            path="/notes/{en_note_guid}/copy",
            visible_fields=["en_note_guid", "en_notebook_guid"],
            body_builder=lambda v: {"targetNotebookGuid": getattr(v, "en_notebook_guid", "") or ""},
        ),
        OpSpec(
            id="search_notes",
            label="Search Notes",
            method="POST",
            path="/notes/search",
            visible_fields=["en_search_query"],
            body_builder=lambda v: {"query": getattr(v, "en_search_query", "") or ""},
        ),
        OpSpec(
            id="get_notebook",
            label="Get Notebook",
            method="GET",
            path="/notebooks/{en_notebook_guid}",
            visible_fields=["en_notebook_guid"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_notebook",
            label="Create Notebook",
            method="POST",
            path="/notebooks",
            visible_fields=["en_notebook_body"],
            body_builder=lambda v: getattr(v, "en_notebook_body", None) or {},
        ),
        OpSpec(
            id="create_tag",
            label="Create Tag",
            method="POST",
            path="/tags",
            visible_fields=["en_tag_name"],
            body_builder=lambda v: {"name": getattr(v, "en_tag_name", "") or ""},
        ),
        OpSpec(
            id="list_tags",
            label="List Tags",
            method="GET",
            path="/tags",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
