"""Best-effort artifact detection from arbitrary node output_data shapes.

Runs after every node in the workflow_runner. If the node already
attached explicit ``artifacts``, we leave them alone. Otherwise we walk
common shapes and synthesise one — free canvas rendering for nodes that
never knew about the contract.

Rules (first match wins):
- ``{image_url, ...}``           → image
- ``{preview_url, ...}``         → url_preview
- ``{code, language, ...}``      → code
- ``{file_url, filename, ...}``  → file
- ``{markdown, ...}``            → markdown
- ``{urls: [str, ...]}``         → one url_preview per url
- ``{artifacts: [dict, ...]}``   → dicts already shaped as Artifacts
"""

from __future__ import annotations

from typing import Any

from apps.api.app.node_system.base.artifact import (
    Artifact,
    make_code,
    make_file,
    make_image,
    make_markdown,
    make_url_preview,
)

# Node keys already documented to hold typed artifacts — pull straight through.
_INLINE_ARTIFACT_KEY = "artifacts"


def detect_artifacts(
    output_data: dict[str, Any], source_node_id: str | None = None
) -> list[Artifact]:
    """Return artifacts synthesised from ``output_data``.

    Best-effort: if nothing matches, returns an empty list. Nodes with a
    genuinely typed output field should attach ``artifacts`` themselves
    instead of relying on detection.
    """
    if not isinstance(output_data, dict):
        return []

    out: list[Artifact] = []

    inline = output_data.get(_INLINE_ARTIFACT_KEY)
    if isinstance(inline, list):
        for entry in inline:
            if isinstance(entry, Artifact):
                out.append(entry)
            elif isinstance(entry, dict) and entry.get("type"):
                try:
                    out.append(Artifact(**entry))
                except Exception:  # noqa: BLE001
                    continue

    image_url = output_data.get("image_url") or output_data.get("imageUrl")
    if isinstance(image_url, str) and image_url.startswith(("http://", "https://", "data:")):
        alt = output_data.get("alt") or output_data.get("caption")
        out.append(make_image(image_url, alt=alt))

    preview_url = output_data.get("preview_url") or output_data.get("previewUrl")
    if isinstance(preview_url, str) and preview_url.startswith(("http://", "https://")):
        out.append(
            make_url_preview(
                preview_url,
                title=output_data.get("title"),
                description=output_data.get("description"),
            )
        )

    code = output_data.get("code")
    if isinstance(code, str) and code.strip():
        language = str(output_data.get("language") or output_data.get("lang") or "text")
        filename = output_data.get("filename")
        out.append(
            make_code(
                code, language=language, filename=filename if isinstance(filename, str) else None
            )
        )

    file_url = output_data.get("file_url") or output_data.get("fileUrl")
    filename = output_data.get("filename")
    if isinstance(file_url, str) and isinstance(filename, str):
        out.append(
            make_file(
                file_url,
                filename=filename,
                mime=str(
                    output_data.get("mime")
                    or output_data.get("content_type")
                    or "application/octet-stream"
                ),
                size_bytes=int(output_data.get("size_bytes") or 0),
            )
        )

    markdown = output_data.get("markdown")
    if isinstance(markdown, str) and markdown.strip():
        out.append(make_markdown(markdown, title=output_data.get("title")))

    urls = output_data.get("urls")
    if isinstance(urls, list):
        for u in urls:
            if isinstance(u, str) and u.startswith(("http://", "https://")):
                out.append(make_url_preview(u))

    if source_node_id:
        out = [a.with_source(source_node_id) for a in out]
    return out
