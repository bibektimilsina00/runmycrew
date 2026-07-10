"""Lock down every registered node's metadata shape.

Phase 0 of the sim-parity roadmap (see `docs/sim-parity-roadmap.md`)
ports hand-written integration nodes onto a manifest scaffold. The
scaffold MUST produce metadata identical to what the hand-written class
produced — otherwise downstream consumers (inspector schema, expression
autocomplete, validation) silently shift behavior.

This test locks the shape three ways:

1. **Structural invariants** — every node has a non-empty `type`, a
   recognized category, declares its `outputs_schema` as a list of
   `{label, type}` dicts, and so on.
2. **Property well-formedness** — each row in `properties` has at least
   `name`, `label`, `type`; condition blocks reference fields that exist.
3. **Snapshot diff** — a JSON snapshot of every node's metadata lives in
   `tests/fixtures/node_metadata_snapshot.json`. Reads compare; writes
   only happen when `RMC_UPDATE_NODE_SNAPSHOTS=1` is set in the env.
   First runs (or new nodes) without that flag fail loud so port-time
   drift surfaces.

When a deliberate metadata change ships (new op, new field, new node),
re-run with `RMC_UPDATE_NODE_SNAPSHOTS=1 pytest …` to refresh the
fixture and commit the diff.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from apps.api.app.node_system.registry.registry import node_registry

SNAPSHOT_PATH = Path(__file__).parent / "fixtures" / "node_metadata_snapshot.json"
UPDATE_FLAG = "RMC_UPDATE_NODE_SNAPSHOTS"

_VALID_CATEGORIES = {"action", "ai", "integration", "logic", "trigger"}
# Scaffold-form scalars + the suite of custom widgets the inspector
# already recognizes. Add to this set when a new custom widget ships
# (`gforms-response`, etc.) — keeping it explicit prevents typo-driven
# silent drift.
_VALID_FIELD_TYPES = {
    "app-link",
    "boolean",
    "code",
    "collection",
    "credential",
    "credentials",
    "datetime",
    "file-list",
    "ga4-property",
    "gchat-space",
    "gcs-bucket",
    "gdrive-folder",
    "gmail-query",
    "google-file",
    "gpeople-group",
    "gsc-site",
    "gsheet-tab",
    "gtasks-tasklist",
    "json",
    "key-value",
    "list",
    "media",
    "messages",
    "meta-resource",
    "number",
    "options",
    "persona-picker",
    "skill-selector",
    "string",
    "tool-selector",
    "wa-template",
    "youtube-channel",
    "youtube-playlist",
    "youtube-video",
}


def _all_metadata() -> dict[str, dict[str, Any]]:
    """Snapshot every registered node's metadata as a plain dict."""
    return {
        node_type: cls.get_metadata().model_dump()
        for node_type, cls in sorted(node_registry._nodes.items())
    }


def test_every_node_has_minimum_metadata():
    """Every registered node carries the minimum metadata the inspector
    relies on."""
    for node_type, cls in node_registry._nodes.items():
        m = cls.get_metadata()
        assert m.type == node_type, f"{node_type}: registry key vs metadata.type mismatch"
        assert m.name, f"{node_type}: empty name"
        assert m.category in _VALID_CATEGORIES, (
            f"{node_type}: unknown category {m.category!r} (valid={_VALID_CATEGORIES})"
        )
        assert m.description, f"{node_type}: empty description"
        assert isinstance(m.properties, list), f"{node_type}: properties not a list"
        assert isinstance(m.outputs_schema, list), f"{node_type}: outputs_schema not a list"


def test_property_rows_are_well_formed():
    """Every row in `properties` carries name/label/type plus a
    recognized `type` value. Condition blocks reference field names that
    actually exist on the same node."""
    for node_type, cls in node_registry._nodes.items():
        m = cls.get_metadata()
        names = {p.get("name") for p in m.properties if isinstance(p, dict)}
        for row in m.properties:
            assert isinstance(row, dict), f"{node_type}: non-dict property row {row!r}"
            assert row.get("name"), f"{node_type}: property row missing name"
            assert row.get("label"), f"{node_type}: property {row['name']!r} missing label"
            assert row.get("type") in _VALID_FIELD_TYPES, (
                f"{node_type}: property {row['name']!r} has unknown type {row.get('type')!r}"
            )
            cond = row.get("condition")
            if isinstance(cond, dict) and "field" in cond:
                assert cond["field"] in names, (
                    f"{node_type}: property {row['name']!r} condition references "
                    f"unknown field {cond['field']!r}"
                )


def test_outputs_schema_rows_are_label_type_pairs():
    for node_type, cls in node_registry._nodes.items():
        m = cls.get_metadata()
        for row in m.outputs_schema:
            assert isinstance(row, dict), f"{node_type}: non-dict outputs_schema row {row!r}"
            assert "label" in row and "type" in row, (
                f"{node_type}: outputs_schema row missing label/type — got {row!r}"
            )


def test_metadata_snapshot_locked():
    """Compare every node's metadata against the on-disk snapshot.

    Refresh via `RMC_UPDATE_NODE_SNAPSHOTS=1 pytest tests/test_node_metadata_snapshot.py`.
    Commit the regenerated fixture alongside whatever change prompted the
    diff so reviewers can see it.
    """
    current = _all_metadata()

    if os.environ.get(UPDATE_FLAG) == "1":
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        pytest.skip(f"Snapshot refreshed at {SNAPSHOT_PATH} ({UPDATE_FLAG}=1).")

    if not SNAPSHOT_PATH.exists():
        pytest.fail(
            f"Snapshot file missing at {SNAPSHOT_PATH}. "
            f"Run `{UPDATE_FLAG}=1 pytest tests/test_node_metadata_snapshot.py` "
            "to create it, then commit the result."
        )

    stored = json.loads(SNAPSHOT_PATH.read_text())
    added = sorted(set(current) - set(stored))
    removed = sorted(set(stored) - set(current))
    changed: list[str] = []
    for node_type in sorted(set(current) & set(stored)):
        if current[node_type] != stored[node_type]:
            changed.append(node_type)

    if added or removed or changed:
        msg = ["Node metadata drift detected:"]
        if added:
            msg.append(f"  added:   {added}")
        if removed:
            msg.append(f"  removed: {removed}")
        if changed:
            msg.append(f"  changed: {changed}")
        msg.append(
            f"\nIf intentional: `{UPDATE_FLAG}=1 pytest "
            "tests/test_node_metadata_snapshot.py` then commit the fixture."
        )
        pytest.fail("\n".join(msg))
