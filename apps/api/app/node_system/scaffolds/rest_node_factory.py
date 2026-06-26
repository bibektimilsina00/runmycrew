"""Build a `BaseNode` subclass from a `ProviderManifest`.

The factory is the heart of the REST scaffold. It owns three things:

1. **Property model synthesis.** Walks the manifest's `fields` list and
   builds a Pydantic model where every field is Optional with a sensible
   default. The model also accepts the implicit `credential` +
   `operation` keys the inspector emits.
2. **Inspector schema build.** Projects manifest fields back into the
   dict shape the inspector consumes, and prepends `credential` +
   `operation` rows. The credential row gets a `notIn public_ops`
   visibility rule so public-read ops hide auth. Each user field gets a
   `condition` derived from the op's `visible_fields` list (unless the
   manifest already supplied one).
3. **Dispatch.** Generates an `execute()` that routes by op id. Each op
   either falls through to `rest_request` (declarative form) or invokes
   a `CustomHandler` (custom form). All exceptions are caught and
   surfaced as structured `NodeResult` failures.

The resulting class can be registered in `node_registry` like any
hand-written node — `node_registry.register(build_rest_node(MANIFEST))`.
"""

from __future__ import annotations

from typing import Any, get_args, get_origin

import httpx
from pydantic import BaseModel, ConfigDict, create_model

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.scaffolds.field_resolvers import (
    pick_props,
    resolve_dict,
    resolve_template,
)
from apps.api.app.node_system.scaffolds.rest_dispatch import (
    RESTError,
    get_flatten,
    rest_request,
)
from apps.api.app.node_system.scaffolds.rest_manifest import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

logger = get_logger(__name__)


_TYPE_ANNOTATIONS: dict[str, Any] = {
    "string": str | None,
    "number": float | None,
    "boolean": bool | None,
    "options": str | None,
    "credential": str | None,
    "json": Any,
}


def _synth_properties_model(manifest: ProviderManifest) -> type[BaseModel]:
    """Build a Pydantic v2 model covering every field the manifest declares
    plus the implicit `credential` + `operation` keys."""
    defs: dict[str, tuple[Any, Any]] = {}

    # Implicit keys — every manifest-built node carries them.
    defs["credential"] = (str | None, None)
    default_op = manifest.operations[0].id if manifest.operations else ""
    defs["operation"] = (str, default_op)

    seen: set[str] = {"credential", "operation"}
    for field in manifest.fields:
        if field.name in seen:
            continue
        seen.add(field.name)
        annotation = _TYPE_ANNOTATIONS.get(field.type, Any)
        defs[field.name] = (annotation, field.default)

    model = create_model(
        f"{manifest.name.replace(' ', '')}Properties",
        __config__=ConfigDict(extra="ignore"),
        **defs,
    )
    return model


def _build_properties_schema(manifest: ProviderManifest) -> list[dict[str, Any]]:
    """Build the list[dict] inspector schema for `NodeMetadata.properties`.

    Injects the credential row (hidden on public ops) and the operation
    dropdown ahead of the user fields. Applies a per-op visibility
    condition to each field unless the manifest already supplied one.
    """
    schema: list[dict[str, Any]] = []

    # Credential row — skip when there's no credential_type at all.
    if manifest.credential_type:
        cred_row: dict[str, Any] = {
            "name": "credential",
            "label": f"{manifest.name} Account",
            "type": "credential",
            "credentialType": manifest.credential_type,
            "required": True,
        }
        if manifest.public_ops:
            cred_row["condition"] = {
                "field": "operation",
                "operator": "notIn",
                "value": list(manifest.public_ops),
            }
        schema.append(cred_row)

    # Operation dropdown.
    schema.append(
        {
            "name": "operation",
            "label": "Operation",
            "type": "options",
            "default": manifest.operations[0].id if manifest.operations else "",
            "options": [{"label": op.label, "value": op.id} for op in manifest.operations],
        }
    )

    # Build a `field_name -> [op_ids]` map from each op's visible_fields,
    # then attach a visibility condition to any user field whose name
    # appears in that map (unless the field already has one).
    visibility: dict[str, list[str]] = {}
    for op in manifest.operations:
        for field_name in op.visible_fields:
            visibility.setdefault(field_name, []).append(op.id)

    for field in manifest.fields:
        row = field.to_inspector_dict()
        if "condition" not in row:
            ops_for_field = visibility.get(field.name)
            if ops_for_field:
                row["condition"] = {"field": "operation", "value": ops_for_field}
        schema.append(row)

    return schema


def _resolve_token(node: Any, manifest: ProviderManifest) -> str | None:
    """Pick the first non-empty token off the injected credential.

    Manifest declares which credential keys to try (`api_key`,
    `access_token`, …) so the same scaffold supports OAuth and API-key
    creds without per-provider code.
    """
    if not node.credential:
        return None
    candidates = manifest.token_field
    keys = candidates if isinstance(candidates, list) else [candidates]
    for key in keys:
        value = node.credential.get(key)
        if value:
            return str(value)
    return None


def _op_index(manifest: ProviderManifest) -> dict[str, OpSpec]:
    return {op.id: op for op in manifest.operations}


def _flatten_output(op: OpSpec, body: Any, props: Any) -> Any:
    """Apply the op's named flattener (if any), then optionally project
    into a static success template defined on the op."""
    fn = get_flatten(op.output_flatten)
    if fn is not None:
        body = fn(body)
    if op.success_payload_template:
        # Substitute placeholders in the static template — the template
        # can reference `{record_id}` etc. so the op response can be
        # embellished with prop context (e.g. "deleted: true, id: …").
        rendered = resolve_dict(op.success_payload_template, props)
        if isinstance(body, dict):
            return {**body, **rendered}
        # Body wasn't a dict — return the rendered template alone.
        return rendered
    return body


async def _dispatch_declarative(
    node: Any,
    client: httpx.AsyncClient,
    manifest: ProviderManifest,
    op: OpSpec,
    token: str | None,
) -> NodeResult:
    """Execute a declarative op against the wire."""
    if not op.method or not op.path:
        return NodeResult(
            success=False,
            error=f"Op {op.id!r} is missing method/path and has no custom handler.",
        )
    url = manifest.base_url + resolve_template(op.path, node.props)
    params = (
        op.query_builder(node.props)
        if op.query_builder is not None
        else pick_props(node.props, op.query_fields)
    )
    body: Any = None
    if op.body_builder is not None:
        body = op.body_builder(node.props)
    elif op.body_fields or op.body_template:
        body = pick_props(node.props, op.body_fields)
        if op.body_template:
            body = {**body, **resolve_dict(op.body_template, node.props)}

    raw, _headers = await rest_request(
        client,
        method=op.method,
        url=url,
        manifest=manifest,
        token=token,
        params=params,
        json=body,
    )
    output = _flatten_output(op, raw, node.props)
    # NodeResult.output_data is `dict[str, Any]` — the scaffold has to
    # normalize any non-dict response so providers that return raw
    # lists (Hacker News id lists), scalars (max-item endpoints), or
    # 204 No Content (Postmark/SendGrid sends) all flow through.
    if output is None:
        output = {"empty": True}
    elif isinstance(output, list):
        output = {"items": output, "count": len(output)}
    elif not isinstance(output, dict):
        output = {"value": output}
    return NodeResult(success=True, output_data=output)


def build_rest_node(manifest: ProviderManifest) -> type[BaseNode]:
    """Build a registered-style `BaseNode` subclass from a manifest.

    The returned class is ready to drop into `node_registry.register(...)`
    with no further wiring.
    """
    Properties = _synth_properties_model(manifest)
    properties_schema = _build_properties_schema(manifest)
    op_table = _op_index(manifest)
    public_ops_set = set(manifest.public_ops)

    metadata = NodeMetadata(
        type=manifest.type,
        name=manifest.name,
        category=manifest.category,
        description=manifest.description,
        properties=properties_schema,
        inputs=manifest.inputs,
        outputs=manifest.outputs,
        icon=manifest.icon_slug or "Circle",
        color=manifest.color,
        outputs_schema=manifest.outputs_schema,
        allow_error=manifest.allow_error,
        credential_type=manifest.credential_type,
    )

    class _ManifestNode(BaseNode[Properties]):  # type: ignore[valid-type]
        _manifest = manifest

        @classmethod
        def get_properties_model(cls) -> type[BaseModel]:
            return Properties

        @classmethod
        def get_metadata(cls) -> NodeMetadata:
            return metadata

        async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
            op_id = getattr(self.props, "operation", None) or (
                manifest.operations[0].id if manifest.operations else ""
            )
            op = op_table.get(op_id)
            if op is None:
                return NodeResult(success=False, error=f"Unknown operation: {op_id}")

            token: str | None = None
            if op.id not in public_ops_set and manifest.credential_type:
                token = _resolve_token(self, manifest)
                if not token:
                    return NodeResult(
                        success=False,
                        error=f"{manifest.name} credential required for this operation.",
                    )

            try:
                async with httpx.AsyncClient(timeout=manifest.timeout_seconds) as client:
                    if op.handler is not None:
                        # Custom op — hand the live node + client + the
                        # auth header dict the scaffold prepared so the
                        # handler can build its own request shape (GraphQL
                        # body, multipart upload, …) without rebuilding
                        # the auth wiring.
                        from apps.api.app.node_system.scaffolds.rest_dispatch import build_auth

                        auth_headers, _ = build_auth(
                            token=token,
                            scheme=manifest.auth,
                            header_name=manifest.auth_header_name,
                            value_template=manifest.auth_value_template,
                            query_param=manifest.auth_query_param,
                        )
                        result = await op.handler(self, client, auth_headers)
                        if not isinstance(result, NodeResult):
                            return NodeResult(success=True, output_data=result)
                        return result
                    return await _dispatch_declarative(self, client, manifest, op, token)
            except RESTError as exc:
                return NodeResult(
                    success=False,
                    error=f"{manifest.name} API error {exc.status}: {exc.message}",
                )
            except httpx.HTTPError as exc:
                return NodeResult(success=False, error=f"{manifest.name} network error: {exc}")
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "%s op=%s failed: %s",
                    manifest.type,
                    op.id,
                    exc,
                    exc_info=True,
                )
                return NodeResult(success=False, error=str(exc))

    _ManifestNode.__name__ = f"{manifest.name.replace(' ', '')}Node"
    _ManifestNode.__qualname__ = _ManifestNode.__name__
    return _ManifestNode


# Mark imports used by callers so linters don't strip them on tightening.
__all__ = [
    "FieldSpec",
    "OpSpec",
    "ProviderManifest",
    "build_rest_node",
]


def _unused_keep(_x: Any) -> Any:
    # Silence "imported but unused" on tooling that doesn't track __all__.
    return (get_args, get_origin)
