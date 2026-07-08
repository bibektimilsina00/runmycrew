"""Serves brand icons from the node system. See ``service.py``."""

import re

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse

from apps.api.app.features.icons.service import resolve_icon_path

router = APIRouter()

# Slugs are node icon names / provider icon_slugs: lowercase alnum + - _ only.
# Reject anything else outright (also blocks path-traversal attempts).
_SLUG_RE = re.compile(r"^[a-z0-9_-]+$")

# Miss responses tell the browser NEVER to cache. Otherwise the first
# 404 (before an SVG is dropped in) sticks around long after the icon
# exists — user sees a blank tile until they hard-refresh. Hits get a
# short cache so common browsing doesn't hammer the disk.
_MISS_HEADERS = {"Cache-Control": "no-store"}
_HIT_HEADERS = {"Cache-Control": "public, max-age=300"}
_MEDIA_TYPES = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".webp": "image/webp",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


@router.get("/{slug}")
async def get_icon(slug: str, response: Response) -> FileResponse:
    name = slug.lower()
    for ext in _MEDIA_TYPES:
        if name.endswith(ext):
            name = name[: -len(ext)]
            break
    if not _SLUG_RE.match(name):
        response.headers.update(_MISS_HEADERS)
        raise HTTPException(status_code=404, detail="Not found", headers=_MISS_HEADERS)
    path = resolve_icon_path(name)
    if not path:
        raise HTTPException(status_code=404, detail="Icon not found", headers=_MISS_HEADERS)
    ext = "." + path.rsplit(".", 1)[-1].lower()
    return FileResponse(
        path,
        media_type=_MEDIA_TYPES.get(ext, "application/octet-stream"),
        headers=_HIT_HEADERS,
    )
