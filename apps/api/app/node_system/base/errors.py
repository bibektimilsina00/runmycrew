"""Structured error payload — generic helper any node can use.

The runtime keeps ``NodeResult.error`` as a plain string so we don't
have to migrate persisted execution rows or bump the websocket schema.
To carry richer error UX, we serialise a small JSON payload behind a
sentinel prefix:

    __fuse_err_v1__{"title": "...", "summary": "...", "actions": ["...", ...], "raw": "..."}

The frontend's ``ErrorView`` recognises the sentinel and renders a
structured card (title + plain-English summary + bulleted actions +
collapsible raw response). Errors without the sentinel keep rendering
the way they always did — single-line headline + JSON tree.

This lets any node (Google, Meta, Slack, custom) opt in to the
richer UX one error path at a time without a framework change.
"""

from __future__ import annotations

import json

# Bump the version suffix if we ever change the JSON shape. The
# frontend can branch on it; we never silently break payloads.
STRUCTURED_ERROR_SENTINEL = "__fuse_err_v1__"


def make_structured_error(
    title: str,
    *,
    summary: str = "",
    actions: list[str] | None = None,
    raw: str = "",
    severity: str = "error",
) -> str:
    """Build the sentinel-prefixed string the frontend renders as a
    structured error card.

    Args:
        title: Short headline — what failed. One sentence. Shown bold.
        summary: Plain-English explanation of *why* it failed and what
            the cause likely is. 1–2 sentences. No jargon.
        actions: Bulleted list of concrete steps the user should take.
            Each item ≤ ~80 characters so it fits one line in the UI.
        raw: The unmodified upstream error body (API response, stack
            trace excerpt, etc). Rendered inside a collapsible
            ``<details>``-style block so power users can debug without
            the noise dominating the card.
        severity: ``"error"`` (default) or ``"warning"``. Drives the
            colour palette on the card.

    Returns:
        A single string suitable for ``NodeResult.error``. Existing
        callers that pass plain strings are unaffected.
    """
    payload = {
        "title": title,
        "summary": summary,
        "actions": actions or [],
        "raw": raw,
        "severity": severity,
    }
    # ensure_ascii=False so non-Latin titles / actions survive the
    # round-trip; the websocket frame is UTF-8 either way.
    return STRUCTURED_ERROR_SENTINEL + json.dumps(payload, ensure_ascii=False)
