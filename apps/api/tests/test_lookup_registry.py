"""Every field manifest that declares `remote=RemoteLookup(...)` must
resolve to a registered handler. Runs in CI so a missing handler is
caught at the same moment as a stray annotation — never at runtime
when a user opens the dropdown.
"""

from __future__ import annotations

import pytest

from apps.api.app.features.credentials.lookups import LOOKUP_REGISTRY
from apps.api.app.node_system.registry.registry import node_registry


def _iter_remote_fields():
    """Yield every (node_type, field_name, provider, resource) row
    from the metadata registry that has a `remote` block. Uses the
    dumped node metadata dict (same shape the API returns) so we cover
    both hand-written and scaffold-generated nodes uniformly.
    """
    for meta in node_registry.list_nodes():
        for prop in meta.get("properties", []) or []:
            remote = prop.get("remote")
            if not isinstance(remote, dict):
                continue
            yield (
                meta.get("type", "?"),
                prop.get("name", "?"),
                remote.get("provider", ""),
                remote.get("resource", ""),
            )


def test_every_remote_field_has_a_handler():
    missing: list[str] = []
    for node_type, field, provider, resource in _iter_remote_fields():
        if not provider or not resource:
            missing.append(f"{node_type}.{field}: empty provider/resource")
            continue
        if resource not in LOOKUP_REGISTRY.get(provider, {}):
            missing.append(f"{node_type}.{field} → {provider}:{resource}")

    if missing:
        pytest.fail(
            "Remote-picker fields point at handlers that aren't registered:\n  - "
            + "\n  - ".join(missing)
        )


def test_lookup_registry_is_populated():
    """Sanity check — if the auto-discovery walk returns nothing the
    whole feature is broken. Also protects against an accidental
    `nodes/` layout regression removing the discovery target."""
    assert LOOKUP_REGISTRY, "Lookup registry is empty — check nodes/**/lookups.py discovery"


def test_remote_depends_on_reference_real_fields():
    """`depends_on` names must match sibling field names on the same
    node — otherwise the frontend waits forever for a value that will
    never arrive."""
    problems: list[str] = []
    for meta in node_registry.list_nodes():
        properties = meta.get("properties", []) or []
        field_names = {p.get("name") for p in properties}
        for prop in properties:
            remote = prop.get("remote")
            if not isinstance(remote, dict):
                continue
            for dep in remote.get("depends_on", []) or []:
                if dep not in field_names:
                    problems.append(
                        f"{meta.get('type')}.{prop.get('name')} depends_on '{dep}' "
                        f"which isn't a sibling field on this node"
                    )
    if problems:
        pytest.fail("Broken `depends_on` references:\n  - " + "\n  - ".join(problems))
