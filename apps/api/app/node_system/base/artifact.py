"""First-class artifact contract shared by every node.

An ``Artifact`` is a typed, renderable output that a node emits alongside
its plain ``output_data``. Downstream consumers (chat app canvas, run
log inspector, evaluator dashboards) pattern-match on ``type`` and route
to the right renderer without having to guess a shape.

Nodes may emit artifacts explicitly by attaching them to
``NodeResult.artifacts``, OR the workflow runner will synthesise them
from known ``output_data`` shapes at post-node time (see
``artifact_detection.py``). Zero-config for existing nodes.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ArtifactType = Literal[
    "markdown",
    "code",
    "image",
    "url_preview",
    "iframe",
    "html",
    "file",
    "audio",
    "video",
    "json",
    "table",
    "chart",
    "citation",
    "pdf",
]


class Artifact(BaseModel):
    """One renderable payload emitted by a node.

    Frontend picks a renderer by ``type``. ``data`` shape is type-specific
    (see docs/apps-artifacts.md). ``metadata`` is provenance the UI can
    show hover-side (source node, mime, size).
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ArtifactType
    title: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    render_hint: Literal["canvas", "inline", "sidebar"] | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    def with_source(self, node_id: str) -> Artifact:
        """Return a copy with ``source_node_id`` stamped in metadata."""
        meta = {**self.metadata, "source_node_id": node_id}
        return self.model_copy(update={"metadata": meta})


def make_markdown(content: str, title: str | None = None) -> Artifact:
    return Artifact(type="markdown", title=title, data={"content": content})


def make_code(code: str, language: str = "text", filename: str | None = None) -> Artifact:
    return Artifact(
        type="code",
        title=filename,
        data={"code": code, "language": language, "filename": filename},
    )


def make_image(
    url: str, alt: str | None = None, width: int | None = None, height: int | None = None
) -> Artifact:
    return Artifact(
        type="image",
        data={"url": url, "alt": alt, "width": width, "height": height},
    )


def make_url_preview(
    url: str, title: str | None = None, description: str | None = None
) -> Artifact:
    return Artifact(
        type="url_preview",
        title=title,
        data={"url": url, "title": title, "description": description},
    )


def make_file(
    url: str, filename: str, mime: str = "application/octet-stream", size_bytes: int = 0
) -> Artifact:
    return Artifact(
        type="file",
        title=filename,
        data={"url": url, "filename": filename, "mime": mime, "size_bytes": size_bytes},
    )


def make_citation(url: str, title: str | None, snippet: str | None = None) -> Artifact:
    return Artifact(
        type="citation",
        title=title,
        data={"url": url, "title": title, "snippet": snippet},
        render_hint="inline",
    )


def make_iframe(url: str, title: str | None = None) -> Artifact:
    return Artifact(type="iframe", title=title, data={"url": url, "sandbox": "allow-scripts"})


def make_table(
    columns: list[dict[str, Any]], rows: list[dict[str, Any]], title: str | None = None
) -> Artifact:
    return Artifact(type="table", title=title, data={"columns": columns, "rows": rows})


def make_chart(
    kind: str, series: list[dict[str, Any]], config: dict[str, Any] | None = None
) -> Artifact:
    return Artifact(
        type="chart",
        data={"type": kind, "series": series, "config": config or {}},
    )


def make_json(data: Any, title: str | None = None) -> Artifact:
    return Artifact(type="json", title=title, data={"data": data})
