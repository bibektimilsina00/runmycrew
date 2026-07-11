"""JSONata-based expression engine.

This module is the foundation of the new workflow expression system. It wraps
the `jsonata-python` library with a small Pythonic API that the runner and
nodes can use to evaluate expressions against an execution context.

What this PR ships (PR4)
------------------------
- `$step.path` — sugar that resolves to the upstream item that fed the
  current node (one paired-item hop back).
- `$node('Label').path` — sugar that resolves to the latest item of a named
  ancestor, walking the paired-item chain so the right row is returned
  even after multi-item fan-outs and merges.
- Both sugars are exposed as native JSONata bindings — `$step` as a
  variable, `$node` as a registered function — so they compose with every
  other JSONata feature (filters, maps, `$sum`, etc.).

What is intentionally *not* here yet (later PRs)
------------------------------------------------
- Dispatch on the `=` prefix in property values — PR5.
- Runner integration that constructs this resolver per node execution
  with the graph context populated — PR5.
"""

from __future__ import annotations

from typing import Any

import jsonata

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.node_item import NodeItem, PairedItem

logger = get_logger(__name__)


class ExpressionError(RuntimeError):
    """Raised when a JSONata expression fails to compile or evaluate.

    Carries the original expression string so callers can surface it in logs
    or user-facing errors without re-deriving it.
    """

    def __init__(self, expression: str, cause: BaseException) -> None:
        self.expression = expression
        self.cause = cause
        super().__init__(f"JSONata error in expression {expression!r}: {cause}")


class JsonataResolver:
    """Evaluates JSONata expressions against an execution context.

    Two layers of context flow in:

    1. **Document** (``context``) — the root JSON the expression path-traverses
       (``foo.bar``, ``items[0].name``, ``$sum(...)``). For workflow use this
       is typically the current node's input data.

    2. **Provenance** — ``current_node_id``, ``incoming``, ``node_items``, and
       ``label_to_id`` enable the ``$step`` and ``$node('Label')`` sugars that
       resolve cross-node references through the paired-item chain. When all
       four are omitted the resolver still works — `$step` returns ``None``
       and ``$node`` returns ``None`` for any label.

    Expressions are compiled on every ``evaluate`` call. A future PR can add
    LRU caching keyed on expression text once we have call-volume data to
    justify it; premature caching would just be guessing.
    """

    def __init__(
        self,
        context: dict[str, Any] | None = None,
        *,
        current_node_id: str | None = None,
        incoming: PairedItem | None = None,
        node_items: dict[str, list[NodeItem]] | None = None,
        label_to_id: dict[str, str] | None = None,
        trigger_data: dict[str, Any] | None = None,
        variables: dict[str, Any] | None = None,
        env: dict[str, str] | None = None,
        secrets: dict[str, str] | None = None,
        loop_data: dict[str, Any] | None = None,
    ) -> None:
        self._context: dict[str, Any] = context if context is not None else {}
        self._current_node_id = current_node_id
        self._incoming = incoming
        self._node_items: dict[str, list[NodeItem]] = node_items or {}
        self._label_to_id: dict[str, str] = label_to_id or {}
        # Workflow-wide context bindings (mirror TemplateResolver's namespaces).
        # Each is exposed as a JSONata variable so users can write
        # `=$trigger.body`, `=$vars.count`, `=$env.API_URL`, etc., in any field.
        self._trigger_data: dict[str, Any] = trigger_data or {}
        self._variables: dict[str, Any] = variables or {}
        self._env: dict[str, str] = env or {}
        self._secrets: dict[str, str] = secrets or {}
        self._loop_data: dict[str, Any] = loop_data or {}

    @property
    def context(self) -> dict[str, Any]:
        return self._context

    def evaluate(
        self,
        expression: str,
        bindings: dict[str, Any] | None = None,
    ) -> Any:
        """Compile ``expression`` and evaluate against the stored context.

        Built-in bindings injected for every call:

        - ``$step`` — the immediate upstream item's ``data`` dict, or
          ``None`` if the current node has no recorded incoming row.
        - ``$node(name)`` — a function returning the latest item's ``data``
          for the named ancestor, walking the paired chain from the current
          node back. Returns ``None`` when the label is unknown or no
          ancestor with that label is reachable from the current row.

        Explicit ``bindings`` passed by the caller override the built-ins on
        a name collision.
        """
        try:
            compiled = jsonata.Jsonata(expression)
        except Exception as exc:
            raise ExpressionError(expression, exc) from exc

        compiled.register_lambda("node", self._lookup_node_by_label)

        frame = compiled.create_frame()
        frame.bind("step", self._step_data())
        frame.bind("trigger", self._trigger_data)
        frame.bind("vars", self._variables)
        frame.bind("env", self._env)
        frame.bind("secrets", self._secrets)
        frame.bind("loop", self._loop_data)
        if bindings:
            for name, value in bindings.items():
                frame.bind(name, value)

        try:
            return compiled.evaluate(self._context, frame)
        except Exception as exc:
            raise ExpressionError(expression, exc) from exc

    # ------------------------------------------------------------------
    # Internal: sugar implementations
    # ------------------------------------------------------------------

    def _step_data(self) -> Any:
        """Return the data dict of the item that fed the current node.

        Looks up ``node_items[incoming.source_node_id][incoming.source_item_index]``
        and returns its ``data`` payload. When no incoming provenance was
        supplied (the first node of an orchestrated sub-graph — crew rounds,
        ForEach bodies — or an entry node), falls back to the node's raw
        input: "$step is whatever fed this node" stays true either way.
        """
        if self._incoming is None:
            return self._context if isinstance(self._context, dict) else None
        item = self._lookup_item(self._incoming.source_node_id, self._incoming.source_item_index)
        return item.data if item is not None else None

    def _lookup_node_by_label(self, label: str) -> Any:
        """Backing impl for the ``$node('Label')`` JSONata function.

        Walks the paired-item chain from the current node back through every
        ancestor, stopping when it reaches a node whose display label matches
        ``label``. Returns that item's ``data`` dict. Returns ``None`` when:

        - the label isn't registered in ``label_to_id``
        - the target node isn't reachable from the current row's provenance
        - the current node has no incoming provenance to walk from
        """
        target_id = self._label_to_id.get(label)
        if target_id is None:
            return None
        item = self._walk_to(target_id)
        return item.data if item is not None else None

    def _walk_to(self, target_node_id: str) -> NodeItem | None:
        """Walk the paired-item chain from the current row back to ``target_node_id``.

        Starts from the row that fed the current node (``incoming``) and
        follows each item's ``paired_item`` back until it finds an item
        located at ``target_node_id``. Returns ``None`` when:

        - no incoming row was supplied
        - the chain dead-ends (an item along the way has no paired_item)
        - the chain reaches the end without finding the target

        A visited set protects against pathological loops in malformed
        paired-item metadata.
        """
        if self._incoming is None:
            return None

        node_id = self._incoming.source_node_id
        item_index = self._incoming.source_item_index
        visited: set[tuple[str, int]] = set()

        while True:
            if (node_id, item_index) in visited:
                logger.warning(
                    "Paired-item walk hit a cycle at (%s, %d); aborting", node_id, item_index
                )
                return None
            visited.add((node_id, item_index))

            item = self._lookup_item(node_id, item_index)
            if item is None:
                return None
            if node_id == target_node_id:
                return item
            if item.paired_item is None:
                return None

            node_id = item.paired_item.source_node_id
            item_index = item.paired_item.source_item_index

    def _lookup_item(self, node_id: str, item_index: int) -> NodeItem | None:
        items = self._node_items.get(node_id)
        if not items or item_index < 0 or item_index >= len(items):
            return None
        return items[item_index]
