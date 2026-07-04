"""Google Slides action node — manifest form.

Google Slides API v1 at `https://slides.googleapis.com/v1`. OAuth via
`google_oauth` umbrella (requires `presentations` scope, already in
the base scope list).
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.google_slides",
    name="Google Slides",
    category="integration",
    description="Google Slides — read/write presentations, batch updates, slides/shapes/text CRUD.",
    icon_slug="google_slides",
    color="#F4B400",
    base_url="https://slides.googleapis.com/v1",
    credential_type="google_oauth",
    token_field=["access_token"],
    auth="bearer",
    fields=[
        FieldSpec(name="presentation_id", label="Presentation ID", type="string"),
        FieldSpec(name="page_object_id", label="Page (Slide) Object ID", type="string"),
        FieldSpec(name="object_id", label="Object ID", type="string"),
        FieldSpec(name="title", label="Title / Presentation Title", type="string"),
        FieldSpec(
            name="requests_body",
            label="Requests (JSON array for batchUpdate)",
            type="json",
            default=[],
        ),
        FieldSpec(name="find_text", label="Find Text", type="string"),
        FieldSpec(name="replace_text", label="Replace Text", type="string"),
        FieldSpec(name="match_case", label="Match Case", type="boolean", default=False),
        FieldSpec(name="image_url", label="Image URL", type="string"),
        FieldSpec(name="image_object_id", label="Image Object ID", type="string"),
        FieldSpec(
            name="shape_type", label="Shape Type (TEXT_BOX|RECTANGLE|ELLIPSE|...)", type="string"
        ),
        FieldSpec(name="text_content", label="Text Content", type="string"),
        FieldSpec(
            name="mime_type", label="Export MIME Type", type="string", default="application/pdf"
        ),
        FieldSpec(
            name="thumbnail_mime_type", label="Thumbnail MIME (PNG)", type="string", default="PNG"
        ),
        FieldSpec(
            name="thumbnail_size",
            label="Thumbnail Size (SMALL|MEDIUM|LARGE)",
            type="string",
            default="MEDIUM",
        ),
        FieldSpec(
            name="destination_presentation_id",
            label="Destination Presentation ID (for copy)",
            type="string",
        ),
        FieldSpec(
            name="insertion_index",
            label="Insertion Index (for add_slide)",
            type="number",
            default=0,
        ),
        FieldSpec(
            name="predefined_layout",
            label="Predefined Layout (e.g. BLANK, TITLE_AND_BODY)",
            type="string",
            default="BLANK",
        ),
        FieldSpec(name="location_x", label="Location X (EMU)", type="number", default=0),
        FieldSpec(name="location_y", label="Location Y (EMU)", type="number", default=0),
        FieldSpec(name="size_width", label="Size Width (EMU)", type="number", default=3000000),
        FieldSpec(name="size_height", label="Size Height (EMU)", type="number", default=3000000),
        FieldSpec(name="text_style_body", label="Text Style (JSON)", type="json", default={}),
        FieldSpec(
            name="paragraph_style_body", label="Paragraph Style (JSON)", type="json", default={}
        ),
        FieldSpec(
            name="shape_properties_body", label="Shape Properties (JSON)", type="json", default={}
        ),
        FieldSpec(
            name="page_properties_body", label="Page Properties (JSON)", type="json", default={}
        ),
        FieldSpec(
            name="image_properties_body", label="Image Properties (JSON)", type="json", default={}
        ),
        FieldSpec(name="table_rows", label="Table Rows", type="number", default=2),
        FieldSpec(name="table_columns", label="Table Columns", type="number", default=2),
        FieldSpec(
            name="line_category",
            label="Line Category (STRAIGHT|BENT|CURVED)",
            type="string",
            default="STRAIGHT",
        ),
        FieldSpec(
            name="bullet_preset",
            label="Bullet Preset (BULLET_DISC_CIRCLE_SQUARE|NUMBERED_DIGIT_ALPHA_ROMAN|...)",
            type="string",
            default="BULLET_DISC_CIRCLE_SQUARE",
        ),
        FieldSpec(name="start_index", label="Text Start Index", type="number", default=0),
        FieldSpec(name="end_index", label="Text End Index", type="number", default=0),
        FieldSpec(name="new_index", label="New Position Index", type="number", default=0),
    ],
    operations=[
        # ─── read / write / create ─────────────────────────────────
        OpSpec(
            id="read",
            label="Read Presentation",
            method="GET",
            path="/presentations/{presentation_id}",
            visible_fields=["presentation_id"],
        ),
        OpSpec(
            id="get_page",
            label="Get Slide (Page)",
            method="GET",
            path="/presentations/{presentation_id}/pages/{page_object_id}",
            visible_fields=["presentation_id", "page_object_id"],
        ),
        OpSpec(
            id="create",
            label="Create Presentation",
            method="POST",
            path="/presentations",
            visible_fields=["title"],
            body_builder=lambda v: {"title": getattr(v, "title", "") or ""},
        ),
        OpSpec(
            id="batch_update",
            label="Batch Update (arbitrary requests)",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "requests_body"],
            body_builder=lambda v: {"requests": getattr(v, "requests_body", None) or []},
        ),
        OpSpec(
            id="write",
            label="Write (alias of batch_update)",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "requests_body"],
            body_builder=lambda v: {"requests": getattr(v, "requests_body", None) or []},
        ),
        # ─── copy + export + thumbnail ─────────────────────────────
        OpSpec(
            id="copy_presentation",
            label="Copy Presentation (via Drive)",
            method="POST",
            path="https://www.googleapis.com/drive/v3/files/{presentation_id}/copy",
            visible_fields=["presentation_id", "title"],
            body_builder=lambda v: {"name": getattr(v, "title", None) or None},
        ),
        OpSpec(
            id="export_presentation",
            label="Export Presentation",
            method="GET",
            path="https://www.googleapis.com/drive/v3/files/{presentation_id}/export",
            visible_fields=["presentation_id", "mime_type"],
            query_builder=lambda v: {
                "mimeType": getattr(v, "mime_type", None) or "application/pdf"
            },
        ),
        OpSpec(
            id="get_thumbnail",
            label="Get Slide Thumbnail",
            method="GET",
            path="/presentations/{presentation_id}/pages/{page_object_id}/thumbnail",
            visible_fields=[
                "presentation_id",
                "page_object_id",
                "thumbnail_mime_type",
                "thumbnail_size",
            ],
            query_builder=lambda v: {
                "thumbnailProperties.mimeType": getattr(v, "thumbnail_mime_type", None) or "PNG",
                "thumbnailProperties.thumbnailSize": getattr(v, "thumbnail_size", None) or "MEDIUM",
            },
        ),
        # ─── text replace ──────────────────────────────────────────
        OpSpec(
            id="replace_all_text",
            label="Replace All Text",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "find_text", "replace_text", "match_case"],
            body_builder=lambda v: {
                "requests": [
                    {
                        "replaceAllText": {
                            "containsText": {
                                "text": getattr(v, "find_text", "") or "",
                                "matchCase": bool(getattr(v, "match_case", False)),
                            },
                            "replaceText": getattr(v, "replace_text", "") or "",
                        }
                    }
                ]
            },
        ),
        OpSpec(
            id="replace_all_shapes_with_image",
            label="Replace All Shapes with Image",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "find_text", "image_url", "match_case"],
            body_builder=lambda v: {
                "requests": [
                    {
                        "replaceAllShapesWithImage": {
                            "containsText": {
                                "text": getattr(v, "find_text", "") or "",
                                "matchCase": bool(getattr(v, "match_case", False)),
                            },
                            "imageUrl": getattr(v, "image_url", "") or "",
                        }
                    }
                ]
            },
        ),
        OpSpec(
            id="replace_image",
            label="Replace Image (by object)",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "image_object_id", "image_url"],
            body_builder=lambda v: {
                "requests": [
                    {
                        "replaceImage": {
                            "imageObjectId": getattr(v, "image_object_id", "") or "",
                            "url": getattr(v, "image_url", "") or "",
                        }
                    }
                ]
            },
        ),
        OpSpec(
            id="update_image_properties",
            label="Update Image Properties",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "object_id", "image_properties_body"],
            body_builder=lambda v: {
                "requests": [
                    {
                        "updateImageProperties": {
                            "objectId": getattr(v, "object_id", "") or "",
                            "imageProperties": getattr(v, "image_properties_body", None) or {},
                            "fields": "*",
                        }
                    }
                ]
            },
        ),
        # ─── slides ────────────────────────────────────────────────
        OpSpec(
            id="add_slide",
            label="Add Slide",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "insertion_index", "predefined_layout"],
            body_builder=lambda v: {
                "requests": [
                    {
                        "createSlide": {
                            "insertionIndex": int(getattr(v, "insertion_index", 0) or 0),
                            "slideLayoutReference": {
                                "predefinedLayout": getattr(v, "predefined_layout", None) or "BLANK"
                            },
                        }
                    }
                ]
            },
        ),
        OpSpec(
            id="delete_object",
            label="Delete Object",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "object_id"],
            body_builder=lambda v: {
                "requests": [{"deleteObject": {"objectId": getattr(v, "object_id", "") or ""}}]
            },
        ),
        OpSpec(
            id="duplicate_object",
            label="Duplicate Object",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "object_id"],
            body_builder=lambda v: {
                "requests": [{"duplicateObject": {"objectId": getattr(v, "object_id", "") or ""}}]
            },
        ),
        OpSpec(
            id="reorder_slides",
            label="Reorder Slides",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "object_id", "new_index"],
            body_builder=lambda v: {
                "requests": [
                    {
                        "updateSlidesPosition": {
                            "slideObjectIds": [getattr(v, "object_id", "") or ""],
                            "insertionIndex": int(getattr(v, "new_index", 0) or 0),
                        }
                    }
                ]
            },
        ),
        # ─── shapes + tables + lines + images ──────────────────────
        OpSpec(
            id="add_image",
            label="Add Image",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=[
                "presentation_id",
                "page_object_id",
                "image_url",
                "location_x",
                "location_y",
                "size_width",
                "size_height",
            ],
            body_builder=lambda v: {
                "requests": [
                    {
                        "createImage": {
                            "url": getattr(v, "image_url", "") or "",
                            "elementProperties": {
                                "pageObjectId": getattr(v, "page_object_id", "") or "",
                                "size": {
                                    "width": {
                                        "magnitude": int(
                                            getattr(v, "size_width", 3000000) or 3000000
                                        ),
                                        "unit": "EMU",
                                    },
                                    "height": {
                                        "magnitude": int(
                                            getattr(v, "size_height", 3000000) or 3000000
                                        ),
                                        "unit": "EMU",
                                    },
                                },
                                "transform": {
                                    "scaleX": 1,
                                    "scaleY": 1,
                                    "translateX": int(getattr(v, "location_x", 0) or 0),
                                    "translateY": int(getattr(v, "location_y", 0) or 0),
                                    "unit": "EMU",
                                },
                            },
                        }
                    }
                ]
            },
        ),
        OpSpec(
            id="create_shape",
            label="Create Shape",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "page_object_id", "shape_type"],
            body_builder=lambda v: {
                "requests": [
                    {
                        "createShape": {
                            "shapeType": getattr(v, "shape_type", None) or "TEXT_BOX",
                            "elementProperties": {
                                "pageObjectId": getattr(v, "page_object_id", "") or "",
                                "size": {
                                    "width": {"magnitude": 3000000, "unit": "EMU"},
                                    "height": {"magnitude": 1000000, "unit": "EMU"},
                                },
                                "transform": {
                                    "scaleX": 1,
                                    "scaleY": 1,
                                    "translateX": 0,
                                    "translateY": 0,
                                    "unit": "EMU",
                                },
                            },
                        }
                    }
                ]
            },
        ),
        OpSpec(
            id="create_line",
            label="Create Line",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "page_object_id", "line_category"],
            body_builder=lambda v: {
                "requests": [
                    {
                        "createLine": {
                            "lineCategory": getattr(v, "line_category", None) or "STRAIGHT",
                            "elementProperties": {
                                "pageObjectId": getattr(v, "page_object_id", "") or "",
                                "size": {
                                    "width": {"magnitude": 3000000, "unit": "EMU"},
                                    "height": {"magnitude": 0, "unit": "EMU"},
                                },
                                "transform": {
                                    "scaleX": 1,
                                    "scaleY": 1,
                                    "translateX": 0,
                                    "translateY": 0,
                                    "unit": "EMU",
                                },
                            },
                        }
                    }
                ]
            },
        ),
        OpSpec(
            id="create_table",
            label="Create Table",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "page_object_id", "table_rows", "table_columns"],
            body_builder=lambda v: {
                "requests": [
                    {
                        "createTable": {
                            "rows": int(getattr(v, "table_rows", 2) or 2),
                            "columns": int(getattr(v, "table_columns", 2) or 2),
                            "elementProperties": {
                                "pageObjectId": getattr(v, "page_object_id", "") or "",
                                "size": {
                                    "width": {"magnitude": 5000000, "unit": "EMU"},
                                    "height": {"magnitude": 2000000, "unit": "EMU"},
                                },
                                "transform": {
                                    "scaleX": 1,
                                    "scaleY": 1,
                                    "translateX": 0,
                                    "translateY": 0,
                                    "unit": "EMU",
                                },
                            },
                        }
                    }
                ]
            },
        ),
        # ─── text ops ──────────────────────────────────────────────
        OpSpec(
            id="insert_text",
            label="Insert Text",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "object_id", "text_content", "insertion_index"],
            body_builder=lambda v: {
                "requests": [
                    {
                        "insertText": {
                            "objectId": getattr(v, "object_id", "") or "",
                            "text": getattr(v, "text_content", "") or "",
                            "insertionIndex": int(getattr(v, "insertion_index", 0) or 0),
                        }
                    }
                ]
            },
        ),
        OpSpec(
            id="delete_text",
            label="Delete Text Range",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "object_id", "start_index", "end_index"],
            body_builder=lambda v: {
                "requests": [
                    {
                        "deleteText": {
                            "objectId": getattr(v, "object_id", "") or "",
                            "textRange": {
                                "type": "FIXED_RANGE",
                                "startIndex": int(getattr(v, "start_index", 0) or 0),
                                "endIndex": int(getattr(v, "end_index", 0) or 0),
                            },
                        }
                    }
                ]
            },
        ),
        OpSpec(
            id="update_text_style",
            label="Update Text Style",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "object_id", "text_style_body"],
            body_builder=lambda v: {
                "requests": [
                    {
                        "updateTextStyle": {
                            "objectId": getattr(v, "object_id", "") or "",
                            "style": getattr(v, "text_style_body", None) or {},
                            "fields": "*",
                            "textRange": {"type": "ALL"},
                        }
                    }
                ]
            },
        ),
        OpSpec(
            id="update_paragraph_style",
            label="Update Paragraph Style",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "object_id", "paragraph_style_body"],
            body_builder=lambda v: {
                "requests": [
                    {
                        "updateParagraphStyle": {
                            "objectId": getattr(v, "object_id", "") or "",
                            "style": getattr(v, "paragraph_style_body", None) or {},
                            "fields": "*",
                            "textRange": {"type": "ALL"},
                        }
                    }
                ]
            },
        ),
        OpSpec(
            id="create_paragraph_bullets",
            label="Create Paragraph Bullets",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "object_id", "bullet_preset"],
            body_builder=lambda v: {
                "requests": [
                    {
                        "createParagraphBullets": {
                            "objectId": getattr(v, "object_id", "") or "",
                            "bulletPreset": getattr(v, "bullet_preset", None)
                            or "BULLET_DISC_CIRCLE_SQUARE",
                            "textRange": {"type": "ALL"},
                        }
                    }
                ]
            },
        ),
        OpSpec(
            id="delete_paragraph_bullets",
            label="Delete Paragraph Bullets",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "object_id"],
            body_builder=lambda v: {
                "requests": [
                    {
                        "deleteParagraphBullets": {
                            "objectId": getattr(v, "object_id", "") or "",
                            "textRange": {"type": "ALL"},
                        }
                    }
                ]
            },
        ),
        # ─── properties ────────────────────────────────────────────
        OpSpec(
            id="update_shape_properties",
            label="Update Shape Properties",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "object_id", "shape_properties_body"],
            body_builder=lambda v: {
                "requests": [
                    {
                        "updateShapeProperties": {
                            "objectId": getattr(v, "object_id", "") or "",
                            "shapeProperties": getattr(v, "shape_properties_body", None) or {},
                            "fields": "*",
                        }
                    }
                ]
            },
        ),
        OpSpec(
            id="update_page_properties",
            label="Update Page (Slide) Properties",
            method="POST",
            path="/presentations/{presentation_id}:batchUpdate",
            visible_fields=["presentation_id", "object_id", "page_properties_body"],
            body_builder=lambda v: {
                "requests": [
                    {
                        "updatePageProperties": {
                            "objectId": getattr(v, "object_id", "") or "",
                            "pageProperties": getattr(v, "page_properties_body", None) or {},
                            "fields": "*",
                        }
                    }
                ]
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "presentationId", "type": "string"},
        {"label": "replies", "type": "array"},
    ],
    allow_error=True,
)
