"""Manifest schema for the REST-tool scaffold.

A `ProviderManifest` is a *pure data* description of a REST integration
node: brand identity, base URL, auth scheme, inspector fields, and the
list of operations. The factory in `rest_node_factory.py` turns one of
these into a fully-registered `BaseNode` subclass — no hand-written
dispatch code, no per-op boilerplate.

Manifests can mix declarative + custom ops. For ~85% of real APIs the
declarative form (path + method + query/body fields) is enough. For the
rest — GraphQL providers, multi-call ops, providers that need request
signing — drop in a `CustomHandler` reference and the factory wires it
into the dispatch table alongside the declarative ops.

See `apps/api/app/node_system/nodes/airtable/manifest.py` for a typical
declarative manifest, and `apps/api/app/node_system/nodes/linear/manifest.py`
for one mixing custom GraphQL handlers under the same shape.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ── field / op schema ────────────────────────────────────────────────


class RemoteLookup(BaseModel):
    """Field-level "pull the options from an external API" descriptor.

    When present on a `FieldSpec`, the frontend renders a searchable
    dropdown populated from `/credentials/{cred}/lookup/{provider}/
    {resource}` instead of a plain text input. The backend routes to a
    handler registered under `(provider, resource)` — handlers live in
    `nodes/<...>/lookups.py` and are auto-discovered on boot.

    `params` values may reference sibling fields on the same node with
    `${field_name}` — resolved on the frontend at fetch time and passed
    through as query params.

    `depends_on` names the sibling fields whose value change should
    invalidate the cached options (e.g. Repo depends on Owner). An
    empty list = fetch once per open.

    `allow_manual` (default true) tells the frontend to show a "List
    ↔ Manual" toggle — power users still need to be able to paste an
    exact id or drop in a `{{ expression }}`.
    """

    model_config = ConfigDict(extra="forbid")

    provider: str
    resource: str
    params: dict[str, str] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    allow_manual: bool = True


class FieldSpec(BaseModel):
    """One row in the inspector schema.

    Mirrors the dict shape the inspector already consumes (`name`,
    `label`, `type`, `condition`, `mode`, `loadOptions`, …). Keeping the
    shape identical means manifests can carry every UX nicety the
    hand-written nodes already use — visibility rules, advanced-mode
    fields, dependent dropdowns — without translating through an
    intermediate representation.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    label: str
    type: Literal[
        "string",
        "number",
        "boolean",
        "options",
        "credential",
        "json",
    ]
    required: bool = False
    default: Any = None
    options: list[dict[str, Any]] | None = None
    placeholder: str | None = None
    secret: bool = False
    description: str | None = None
    load_options_url: str | None = None
    load_options_depends_on: list[str] | None = None
    condition: dict[str, Any] | None = None
    mode: Literal["basic", "advanced"] = "basic"
    # When `type == "credential"`. Accepts a list so a node can take
    # either OAuth or an API key for the same provider.
    credential_type: str | list[str] | None = None
    # Turn this string field into a credential-scoped remote picker
    # (See `RemoteLookup`). Optional and additive — a field without
    # `remote` renders as the ordinary string editor. Fields marked
    # `remote` should still declare `type="string"` so the value stays a
    # plain id in the workflow graph.
    remote: RemoteLookup | None = None

    def to_inspector_dict(self) -> dict[str, Any]:
        """Project this spec into the dict shape the inspector reads."""
        d: dict[str, Any] = {"name": self.name, "label": self.label, "type": self.type}
        if self.required:
            d["required"] = True
        if self.default is not None:
            d["default"] = self.default
        if self.options is not None:
            d["options"] = self.options
        if self.placeholder is not None:
            d["placeholder"] = self.placeholder
        if self.secret:
            d["secret"] = True
        if self.description is not None:
            d["description"] = self.description
        if self.load_options_url is not None:
            d["loadOptions"] = self.load_options_url
        if self.load_options_depends_on is not None:
            d["loadOptionsDependsOn"] = self.load_options_depends_on
        if self.condition is not None:
            d["condition"] = self.condition
        if self.mode != "basic":
            d["mode"] = self.mode
        if self.credential_type is not None:
            d["credentialType"] = self.credential_type
        if self.remote is not None:
            d["remote"] = self.remote.model_dump()
        return d


# A custom op handler — receives the live node instance, an httpx client
# (already created by the factory), and the auth header dict the factory
# has prepared. Returns a `NodeResult` or raises.
#
# We accept `Any` for the node here to avoid a circular import with
# BaseNode; the factory passes the real instance at call time.
CustomHandler = Callable[[Any, Any, dict[str, str]], Awaitable[Any]]


class OpSpec(BaseModel):
    """One operation in the dispatch table.

    Two forms are supported under the same shape:

    1. **Declarative** — set `method` + `path` (template) plus
       `query_fields` / `body_fields`. The factory builds the call.
    2. **Custom** — set `handler` to a coroutine. The factory passes the
       prepared client and ignores `method` / `path` / field lists.

    `output_flatten` names a registered flattener that converts the raw
    JSON body into the canonical shape the node's `output_data` advertises.
    Defaults to passthrough (return the body unchanged).
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    id: str
    label: str
    # Visibility — show the credential field unless `public=True`, and
    # show each prop only on the ops listed in `visible_fields`. The
    # factory wires both into the inspector schema's `condition` blocks.
    public: bool = False
    visible_fields: list[str] = Field(
        default_factory=list,
        description="Names of props that should appear in the inspector when this op is selected.",
    )

    # Declarative form.
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"] | None = None
    path: str | None = None
    query_fields: list[str] = Field(default_factory=list)
    body_fields: list[str] = Field(default_factory=list)
    # Static body keys mixed in alongside `body_fields`. Values may
    # reference props via `{prop_name}` substitution.
    body_template: dict[str, Any] | None = None
    # When `query_fields` should be passed under a non-trivial mapping
    # (rename, type cast) the factory accepts a function instead. Most
    # ops won't need this.
    query_builder: Callable[[Any], dict[str, Any]] | None = None
    body_builder: Callable[[Any], dict[str, Any]] | None = None

    # Custom form.
    handler: CustomHandler | None = None

    # Output shaping.
    output_flatten: str | None = None
    success_payload_template: dict[str, Any] | None = None
    # Per-op headers that layer on top of manifest.extra_headers.
    # Needed for AWS JSON-protocol services (SQS, Athena, Secrets
    # Manager) that dispatch by `X-Amz-Target: <Service>.<Action>` —
    # the header changes per operation.
    extra_headers: dict[str, str] = Field(default_factory=dict)


# ── provider manifest ────────────────────────────────────────────────


AuthScheme = Literal[
    "bearer",
    "header_token",
    "basic",
    # Basic auth with the token as username + empty password —
    # `Basic base64(token:)`. Greenhouse's Harvest API uses this.
    # `basic` doesn't fit: it always encodes `username:token`, doubling
    # the api_key if you also put it in `basic_username`.
    "basic_token_only",
    "query_token",
    # AWS Signature V4 — service + region rides on the manifest via
    # `aws_service` + `aws_default_region`; access_key + secret_access_key
    # + optional session_token come from the credential dict.
    "aws_sigv4",
    "none",
]


class ProviderManifest(BaseModel):
    """Top-level manifest for a REST integration node.

    Acts as the *contract* between the scaffold and a provider. Each
    provider lives at `apps/api/app/node_system/nodes/<slug>/manifest.py`
    and exports a `MANIFEST = ProviderManifest(...)` constant the
    package's `__init__.py` hands to `build_rest_node`.
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    # Identity surfaced to the inspector + tile.
    type: str
    name: str
    category: str = "integration"
    description: str
    icon_slug: str | None = None
    color: str = "#1c1c1c"

    # Network base. Concrete request URL = `base_url + op.path` after
    # path-template substitution.
    base_url: str

    # Credential resolution.
    credential_type: str | list[str] | None = None
    # Which key on the decrypted credential carries the token. Most
    # providers store the API key as `api_key`; OAuth credentials use
    # `access_token`. The scaffold tries both in that order if a list is
    # given.
    token_field: str | list[str] = Field(default_factory=lambda: ["api_key", "access_token"])

    # Auth scheme.
    auth: AuthScheme = "bearer"
    auth_header_name: str = "Authorization"
    auth_value_template: str = "Bearer {token}"
    # For `query_token` — name of the URL param the token rides on.
    auth_query_param: str = "api_key"
    # For `basic` only. Empty = `{token}:` base64 (legacy). A literal
    # value (e.g. `"api"` for Mailgun) → `{value}:{token}`. A
    # `{credential_key}` template resolves against the live credential
    # dict — e.g. Twilio uses `"{account_sid}"` to pull the account sid
    # out of the credential and put it on the username side.
    auth_basic_username: str = ""
    # For `aws_sigv4` only. `aws_service` is the SigV4 service name
    # (`s3`, `ses`, `sqs`, `secretsmanager`, `athena`, …). Region
    # resolves from the credential's `region` field first, then falls
    # back to `aws_default_region`. S3 defaults to unsigned payload
    # hashing when body sizes routinely exceed a few MB — set
    # `aws_unsigned_payload=True` on the manifest to opt in.
    aws_service: str = ""
    aws_default_region: str = "us-east-1"
    aws_unsigned_payload: bool = False
    # Optional content-type override (`application/json` is the default).
    content_type: str = "application/json"
    # Extra static headers (e.g. `X-GitHub-Api-Version`).
    extra_headers: dict[str, str] = Field(default_factory=dict)
    # Request timeout, seconds.
    timeout_seconds: float = 30.0

    # Public ops bypass the credential check entirely. The factory hides
    # the credential field in the inspector when the selected op is in
    # this list.
    public_ops: list[str] = Field(default_factory=list)

    # Inspector schema (minus the implicit `credential` + `operation`
    # rows, which the factory injects).
    fields: list[FieldSpec] = Field(default_factory=list)

    # Dispatch table.
    operations: list[OpSpec] = Field(default_factory=list)

    # Outputs schema — the editor's expression autocomplete consumes
    # this. The factory passes it through to NodeMetadata as-is.
    outputs_schema: list[dict[str, Any]] = Field(default_factory=list)

    # When True the engine doesn't halt the workflow on this node's
    # error — the failure surfaces on the node's error output port.
    allow_error: bool = True

    inputs: int = 1
    outputs: int = 1
