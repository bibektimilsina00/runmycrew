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
    color="#ffffff",
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
        FieldSpec(name="pattern", label="Pattern", type="string", default="*"),
        FieldSpec(name="hash_field", label="Hash Field", type="string"),
        FieldSpec(name="hash_value", label="Hash Value", type="string"),
        FieldSpec(name="range_start", label="Range Start", type="number", default=0),
        FieldSpec(name="range_end", label="Range End", type="number", default=-1),
        FieldSpec(
            name="redis_command", label="Redis Command (JSON array)", type="json", default=[]
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
        OpSpec(
            id="hset",
            label="HSET",
            method="POST",
            path="/",
            visible_fields=["redis_key", "hash_field", "hash_value"],
            body_builder=lambda v: [
                "HSET",
                getattr(v, "redis_key", "") or "",
                getattr(v, "hash_field", "") or "",
                getattr(v, "hash_value", "") or "",
            ],
        ),
        OpSpec(
            id="hget",
            label="HGET",
            method="POST",
            path="/",
            visible_fields=["redis_key", "hash_field"],
            body_builder=lambda v: [
                "HGET",
                getattr(v, "redis_key", "") or "",
                getattr(v, "hash_field", "") or "",
            ],
        ),
        OpSpec(
            id="hgetall",
            label="HGETALL",
            method="POST",
            path="/",
            visible_fields=["redis_key"],
            body_builder=lambda v: ["HGETALL", getattr(v, "redis_key", "") or ""],
        ),
        OpSpec(
            id="hdel",
            label="HDEL",
            method="POST",
            path="/",
            visible_fields=["redis_key", "hash_field"],
            body_builder=lambda v: [
                "HDEL",
                getattr(v, "redis_key", "") or "",
                getattr(v, "hash_field", "") or "",
            ],
        ),
        OpSpec(
            id="setnx",
            label="SETNX",
            method="POST",
            path="/",
            visible_fields=["redis_key", "redis_value"],
            body_builder=lambda v: [
                "SETNX",
                getattr(v, "redis_key", "") or "",
                getattr(v, "redis_value", "") or "",
            ],
        ),
        OpSpec(
            id="lpush",
            label="LPUSH",
            method="POST",
            path="/",
            visible_fields=["redis_key", "redis_value"],
            body_builder=lambda v: [
                "LPUSH",
                getattr(v, "redis_key", "") or "",
                getattr(v, "redis_value", "") or "",
            ],
        ),
        OpSpec(
            id="rpush",
            label="RPUSH",
            method="POST",
            path="/",
            visible_fields=["redis_key", "redis_value"],
            body_builder=lambda v: [
                "RPUSH",
                getattr(v, "redis_key", "") or "",
                getattr(v, "redis_value", "") or "",
            ],
        ),
        OpSpec(
            id="lpop",
            label="LPOP",
            method="POST",
            path="/",
            visible_fields=["redis_key"],
            body_builder=lambda v: ["LPOP", getattr(v, "redis_key", "") or ""],
        ),
        OpSpec(
            id="rpop",
            label="RPOP",
            method="POST",
            path="/",
            visible_fields=["redis_key"],
            body_builder=lambda v: ["RPOP", getattr(v, "redis_key", "") or ""],
        ),
        OpSpec(
            id="llen",
            label="LLEN",
            method="POST",
            path="/",
            visible_fields=["redis_key"],
            body_builder=lambda v: ["LLEN", getattr(v, "redis_key", "") or ""],
        ),
        OpSpec(
            id="lrange",
            label="LRANGE",
            method="POST",
            path="/",
            visible_fields=["redis_key", "range_start", "range_end"],
            body_builder=lambda v: [
                "LRANGE",
                getattr(v, "redis_key", "") or "",
                str(getattr(v, "range_start", 0) or 0),
                str(getattr(v, "range_end", -1) or -1),
            ],
        ),
        OpSpec(
            id="persist",
            label="PERSIST",
            method="POST",
            path="/",
            visible_fields=["redis_key"],
            body_builder=lambda v: ["PERSIST", getattr(v, "redis_key", "") or ""],
        ),
        OpSpec(
            id="command",
            label="Arbitrary Command",
            method="POST",
            path="/",
            visible_fields=["redis_command"],
            body_builder=lambda v: getattr(v, "redis_command", []) or [],
        ),
    ],
    outputs_schema=[
        {"label": "result", "type": "string"},
    ],
    allow_error=True,
)
