"""JSONata-based expression engine.

This module is the foundation of the new workflow expression system. It wraps
the `jsonata-python` library with a small Pythonic API that the runner and
nodes can use to evaluate expressions against an execution context.

What this PR ships
------------------
- A thin `JsonataResolver` that compiles a JSONata expression and evaluates it
  against a context document, optionally with variable bindings.
- Nothing else. The resolver is **not wired into the runner yet** — that lands
  in a later PR. Today's existing `TemplateResolver` (regex `{{...}}`) continues
  to handle every workflow.

What is intentionally *not* here yet (later PRs)
------------------------------------------------
- `$step` / `$('Label')` surface sugar — PR4.
- Paired-item chain walking for multi-item nodes — PR4.
- Dispatch on the `=` prefix in property values — PR5.

Keeping the surface minimal now means later PRs can extend it (adding sugar,
bindings, paired-item context) without breaking callers — there are none today.
"""

from __future__ import annotations

from typing import Any

import jsonata

from apps.api.app.core.logger import get_logger

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

    The constructor takes the **root document** that path-style expressions
    (`foo.bar`, `items[0].name`, `$sum(...)`) traverse. Additional variable
    bindings — values referenced as `$name` inside expressions — are passed
    per-call to ``evaluate``.

    Expressions are compiled on every ``evaluate`` call. A future PR can add
    LRU caching keyed on expression text once we have call-volume data to
    justify it; premature caching would just be guessing.
    """

    def __init__(self, context: dict[str, Any] | None = None) -> None:
        self._context: dict[str, Any] = context if context is not None else {}

    @property
    def context(self) -> dict[str, Any]:
        return self._context

    def evaluate(
        self,
        expression: str,
        bindings: dict[str, Any] | None = None,
    ) -> Any:
        """Compile ``expression`` and evaluate against the stored context.

        ``bindings`` keys are bound as JSONata variables — referencing them as
        ``$key`` inside the expression returns the corresponding value. Missing
        path matches return ``None`` (JSONata's "no match"); compile or
        evaluation errors raise :class:`ExpressionError`.
        """
        try:
            compiled = jsonata.Jsonata(expression)
        except Exception as exc:
            raise ExpressionError(expression, exc) from exc

        frame = None
        if bindings:
            frame = compiled.create_frame()
            for name, value in bindings.items():
                frame.bind(name, value)

        try:
            return compiled.evaluate(self._context, frame)
        except Exception as exc:
            raise ExpressionError(expression, exc) from exc
