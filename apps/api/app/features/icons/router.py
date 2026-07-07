"""Serves brand SVGs from the node system. See ``service.py``."""

import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from apps.api.app.features.icons.service import resolve_icon_path

router = APIRouter()

# Slugs are node icon names / provider icon_slugs: lowercase alnum + - _ only.
# Reject anything else outright (also blocks path-traversal attempts).
_SLUG_RE = re.compile(r"^[a-z0-9_-]+$")


@router.get("/{slug}")
async def get_icon(slug: str) -> FileResponse:
    name = slug[:-4] if slug.lower().endswith(".svg") else slug
    name = name.lower()
    if not _SLUG_RE.match(name):
        raise HTTPException(status_code=404, detail="Not found")
    path = resolve_icon_path(name)
    if not path:
        raise HTTPException(status_code=404, detail="Icon not found")
    return FileResponse(
        path,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=3600"},
    )
