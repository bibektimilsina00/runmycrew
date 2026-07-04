"""Build a webhook-trigger `BaseNode` from a `WebhookTriggerManifest`.

A webhook trigger node is *display + state* — it carries the inspector
schema for the user (URL hint, secret field, event filter) and the
property model. All actual delivery handling happens in the shared
`/webhooks/{provider}/...` receiver (`features/webhooks/`).

The factory also registers the manifest in the module-level webhook
manifest registry so the receiver can route by `provider` without
importing any node modules.

Inspector schema (in order):
  1. credential row (optional — only when `credential_type` set)
  2. extra_fields (provider-supplied — owner / repo / project_id / ...)
  3. event dropdown (with the magic `*` "any event" row prepended)
  4. webhook secret (required when `require_secret=True`)
  5. The implicit URL hint description — not a real field, just a
     description on the secret row pointing to the URL pattern.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, create_model

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.scaffolds.webhook_manifest import (
    EVENT_ANY,
    WebhookTriggerManifest,
    register_webhook_manifest,
)

_TYPE_ANNOTATIONS: dict[str, Any] = {
    "string": str | None,
    "number": float | None,
    "boolean": bool | None,
    "options": str | None,
    "credential": str | None,
    "json": Any,
}


def _synth_props(manifest: WebhookTriggerManifest) -> type[BaseModel]:
    """Pydantic model: credential, event filter, secret, extra fields."""
    defs: dict[str, tuple[Any, Any]] = {
        "credential": (str | None, None),
        "event": (str, EVENT_ANY),
        manifest.signature.secret_field: (str, ""),
    }
    for field in manifest.extra_fields:
        if field.name in defs:
            continue
        defs[field.name] = (_TYPE_ANNOTATIONS.get(field.type, Any), field.default)
    return create_model(
        f"{manifest.name.replace(' ', '')}WebhookProperties",
        __config__=ConfigDict(extra="ignore"),
        **defs,
    )


def _build_schema(manifest: WebhookTriggerManifest) -> list[dict[str, Any]]:
    """Inspector schema for the trigger node."""
    schema: list[dict[str, Any]] = []

    if manifest.credential_type:
        schema.append(
            {
                "name": "credential",
                "label": f"{manifest.name} Account (optional)",
                "type": "credential",
                "credentialType": manifest.credential_type,
                "required": False,
                "description": (
                    "Optional — only needed if downstream nodes call "
                    f"{manifest.name} APIs on the same flow."
                ),
            }
        )

    for field in manifest.extra_fields:
        schema.append(field.to_inspector_dict())

    # Event filter dropdown — prepend "Any event" so the manifest
    # author doesn't have to remember to add it themselves.
    options = [{"label": "Any event", "value": EVENT_ANY}] + [
        {"label": e.label, "value": e.value} for e in manifest.events
    ]
    schema.append(
        {
            "name": "event",
            "label": "Event",
            "type": "options",
            "default": EVENT_ANY,
            "options": options,
            "description": (
                f"Filter applied to the `{manifest.event_header}` header. "
                'Pick "Any event" to forward every delivery.'
            ),
        }
    )

    if manifest.require_secret:
        schema.append(
            {
                "name": manifest.signature.secret_field,
                "label": "Webhook Secret",
                "type": "string",
                "secret": True,
                "required": True,
                "placeholder": f"Set the same value in {manifest.name} webhook settings",
                "description": (
                    f"{manifest.signature.scheme.upper()} secret. "
                    f"Deliveries without a valid `{manifest.signature.header_name}` "
                    "header are rejected."
                ),
            }
        )

    return schema


def build_webhook_trigger(manifest: WebhookTriggerManifest) -> type[BaseNode]:
    """Build a registered-style webhook-trigger `BaseNode`."""
    Props = _synth_props(manifest)
    properties = _build_schema(manifest)
    metadata = NodeMetadata(
        type=manifest.type,
        name=manifest.name,
        category=manifest.category,
        description=manifest.description,
        properties=properties,
        inputs=0,
        outputs=1,
        icon=manifest.icon_slug or "Circle",
        color=manifest.color,
        outputs_schema=manifest.outputs_schema,
        allow_error=True,
        credential_type=manifest.credential_type,
    )

    class _ManifestWebhookNode(BaseNode[Props]):  # type: ignore[valid-type]
        _manifest = manifest

        @classmethod
        def get_properties_model(cls) -> type[BaseModel]:
            return Props

        @classmethod
        def get_metadata(cls) -> NodeMetadata:
            return metadata

        async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
            # Receiver dispatched with the payload already shaped; pass
            # it through so downstream nodes see what /listen returned.
            return NodeResult(success=True, output_data=input_data or {})

    _ManifestWebhookNode.__name__ = f"{manifest.name.replace(' ', '')}WebhookTriggerNode"
    _ManifestWebhookNode.__qualname__ = _ManifestWebhookNode.__name__

    register_webhook_manifest(manifest)
    return _ManifestWebhookNode


__all__ = ["build_webhook_trigger"]
