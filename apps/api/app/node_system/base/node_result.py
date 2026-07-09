from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.artifact import Artifact
from apps.api.app.node_system.base.node_item import NodeItem


class NodeResult(BaseModel):
    success: bool
    output_data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    logs: list[str] = Field(default_factory=list)
    # When True the node already dispatched its downstream graph; runner skips edge follow
    handled_successors: bool = False

    # Optional explicit per-item output list for paired-item-aware nodes (fan-out
    # or merges). When None, the runner treats the result as a single item whose
    # `data` is `output_data`. Existing nodes keep returning the legacy shape
    # unchanged — :meth:`get_items` papers over the difference for callers that
    # want a uniform list view.
    items: list[NodeItem] | None = None

    # Typed renderable outputs shown alongside the run log (and in the public
    # app canvas). Nodes may emit these explicitly; the runner will also
    # synthesise them from known output_data shapes at post-node time so
    # legacy nodes get free rendering.
    artifacts: list[Artifact] = Field(default_factory=list)

    def get_items(self) -> list[NodeItem]:
        """Return the items this result represents as a uniform list.

        - If :attr:`items` is set, returns it verbatim (no copy).
        - Otherwise synthesises a single-item list wrapping :attr:`output_data`,
          which matches the implicit shape every node has produced to date.
        """
        if self.items is not None:
            return self.items
        return [NodeItem(data=self.output_data)]
