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
_PURE_PLACEHOLDER_RE = re.compile(r"^\{([a-zA-Z_][a-zA-Z0-9_]*)\}$")


def _stringify(value: Any) -> str:
    """Stringify a substituted value for embedding inside a template.

    Whole-number floats lose the trailing `.0` so `numResults` doesn't
    become `"5.0"` on the wire. Pydantic widens `number` props to float
    which makes `int(value) == value` the right ints-only check.
    """
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


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
        return _stringify(value)

    return _PLACEHOLDER_RE.sub(replace, template)


def resolve_dict(template: dict[str, Any] | None, props: Any) -> dict[str, Any]:
    """Recursively apply `resolve_template` to string leaves of a dict.

    Lists are walked; nested dicts recurse; numbers / booleans pass
    through untouched. Suitable for `body_template` substitution.

    Special case — when a leaf is *exactly* `"{name}"` and the resolved
    prop is a number/bool/list/dict, return the value with its native
    type intact. Otherwise the template would coerce `5` into `"5"` and
    break APIs that type-check (`numResults` expects an int, not a
    string). Multi-placeholder templates (`"{a}-{b}"`) still go through
    the string path since the joined result can't preserve types.
    """

    if not template:
        return {}

    def walk(value: Any) -> Any:
        if isinstance(value, str):
            pure = _PURE_PLACEHOLDER_RE.match(value)
            if pure:
                resolved = getattr(props, pure.group(1), None)
                if resolved is None:
                    return value
                if isinstance(resolved, float) and resolved.is_integer():
                    return int(resolved)
                return resolved
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
