"""Upstash Redis action node — manifest form.

Upstash exposes Redis over HTTP via a per-instance URL (`https://abc-12345.upstash.io`).
The credential carries `rest_url` + `api_key`; the manifest resolves
the rest_url from the credential dict via the scaffold's
`_PropCredView`.

We expose the eight commands that cover 95% of workflow use: GET,
SET, DEL, INCR, EXPIRE, TTL, KEYS, EXISTS. The Upstash convention is
to send each command as a JSON array body: `["SET", key, value]`.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)


def _cmd(*parts: str | None) -> list[str]:
    """Drop None / empty parts so a missing arg doesn't slot into the
    command as an empty string Redis would reject."""
    return [str(p) for p in parts if p not in (None, "")]


MANIFEST = ProviderManifest(
    type="action.upstash_redis",
    name="Upstash Redis",
    category="integration",
    description="Run Redis commands against Upstash via the REST API.",
    icon_slug="upstash",
    color="#1c1c1c",
    base_url="",
    credential_type="upstash_redis_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="key", label="Key", type="string", required=True),
        FieldSpec(name="value", label="Value", type="string"),
        FieldSpec(name="ttl_seconds", label="TTL (seconds)", type="number", mode="advanced"),
        FieldSpec(
            name="pattern", label="Pattern", type="string", placeholder="user:*", mode="advanced"
        ),
        FieldSpec(
            name="increment", label="Increment by", type="number", default=1, mode="advanced"
        ),
    ],
    operations=[
        OpSpec(
            id="get",
            label="GET",
            method="POST",
            path="{rest_url}",
            visible_fields=["key"],
            body_builder=lambda v: _cmd("GET", getattr(v, "key", None)),
        ),
        OpSpec(
            id="set",
            label="SET",
            method="POST",
            path="{rest_url}",
            visible_fields=["key", "value", "ttl_seconds"],
            body_builder=lambda v: (
                _cmd("SET", getattr(v, "key", None), getattr(v, "value", None))
                + (
                    ["EX", str(int(getattr(v, "ttl_seconds", 0) or 0))]
                    if getattr(v, "ttl_seconds", None)
                    else []
                )
            ),
        ),
        OpSpec(
            id="del",
            label="DEL",
            method="POST",
            path="{rest_url}",
            visible_fields=["key"],
            body_builder=lambda v: _cmd("DEL", getattr(v, "key", None)),
        ),
        OpSpec(
            id="incr",
            label="INCR / INCRBY",
            method="POST",
            path="{rest_url}",
            visible_fields=["key", "increment"],
            body_builder=lambda v: (
                _cmd("INCRBY", getattr(v, "key", None), str(int(getattr(v, "increment", 1) or 1)))
                if (getattr(v, "increment", 1) or 1) != 1
                else _cmd("INCR", getattr(v, "key", None))
            ),
        ),
        OpSpec(
            id="expire",
            label="EXPIRE",
            method="POST",
            path="{rest_url}",
            visible_fields=["key", "ttl_seconds"],
            body_builder=lambda v: _cmd(
                "EXPIRE",
                getattr(v, "key", None),
                str(int(getattr(v, "ttl_seconds", 0) or 0)),
            ),
        ),
        OpSpec(
            id="ttl",
            label="TTL",
            method="POST",
            path="{rest_url}",
            visible_fields=["key"],
            body_builder=lambda v: _cmd("TTL", getattr(v, "key", None)),
        ),
        OpSpec(
            id="keys",
            label="KEYS",
            method="POST",
            path="{rest_url}",
            visible_fields=["pattern"],
            body_builder=lambda v: _cmd("KEYS", getattr(v, "pattern", None) or "*"),
        ),
        OpSpec(
            id="exists",
            label="EXISTS",
            method="POST",
            path="{rest_url}",
            visible_fields=["key"],
            body_builder=lambda v: _cmd("EXISTS", getattr(v, "key", None)),
        ),
    ],
    outputs_schema=[
        {"label": "result", "type": "string"},
    ],
    allow_error=True,
)
