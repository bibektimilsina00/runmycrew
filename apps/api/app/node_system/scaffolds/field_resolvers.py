"""Template-string substitution helpers for the REST scaffold.

The manifest declares paths like `/repos/{owner}/{repo}/issues` and
body templates like `{"name": "{table_name}"}`. Resolvers walk those
strings, look up the named props on the live node, and emit concrete
URLs / payloads. Two helpers, both intentionally small — they exist so
the factory doesn't sprout regex code in three places.
"""

from __future__ import annotations

import re
from typing import Any

_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def resolve_template(template: str, props: Any) -> str:
    """Substitute `{name}` placeholders against attributes of `props`.

    Unresolved placeholders pass through unchanged — a missing prop
    surfaces as a recognizable error on the server (`/repos/{owner}/…`
    in the URL) rather than a silent empty string. Caller code that
    cares can scan the result for unresolved `{…}`.
    """

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        value = getattr(props, name, None)
        if value is None:
            return match.group(0)
        return str(value)

    return _PLACEHOLDER_RE.sub(replace, template)


def resolve_dict(template: dict[str, Any] | None, props: Any) -> dict[str, Any]:
    """Recursively apply `resolve_template` to string leaves of a dict.

    Lists are walked; nested dicts recurse; numbers / booleans pass
    through untouched. Suitable for `body_template` substitution.
    """

    if not template:
        return {}

    def walk(value: Any) -> Any:
        if isinstance(value, str):
            return resolve_template(value, props)
        if isinstance(value, dict):
            return {k: walk(v) for k, v in value.items()}
        if isinstance(value, list):
            return [walk(v) for v in value]
        return value

    return walk(template)


def pick_props(props: Any, field_names: list[str]) -> dict[str, Any]:
    """Build a `{name: value}` dict from the named attributes of `props`.

    Skips `None` values so the resulting params dict doesn't carry empty
    query-string keys. Booleans and zero are preserved.
    """
    out: dict[str, Any] = {}
    for name in field_names:
        value = getattr(props, name, None)
        if value is None:
            continue
        out[name] = value
    return out
