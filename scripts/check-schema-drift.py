#!/usr/bin/env python
"""Backend/frontend schema-drift guard for the public-app API.

The frontend's zod schemas (apps/web/src/features/public-app/types/
publicAppTypes.ts) hard-require fields from these responses. Backend
reshapes shipped twice without the frontend noticing until prod (the
`workflow_id: null` crew-session crash was one). This script builds the
FastAPI OpenAPI spec OFFLINE (no server) and asserts every field the
frontend requires still exists — and that fields the frontend types as
non-nullable haven't gone nullable.

The manifest below is the frontend's contract, kept next to this check
on purpose: change the zod schema → change the manifest → this stays
green. Change the backend response model without touching the frontend
→ this goes red in CI before prod does.

Run: uv run --project apps/api python scripts/check-schema-drift.py
"""

from __future__ import annotations

import sys
import warnings

# component name -> {
#   "required": fields the zod schema will crash without,
#   "non_nullable": required fields zod types as NOT accepting null,
# }
FRONTEND_CONTRACT: dict[str, dict[str, list[str]]] = {
    "PublicAppOut": {
        "required": [
            "workflow_id",
            "workspace_slug",
            "app_slug",
            "title",
            "description",
            "mode",
            "auth_mode",
            "config",
        ],
        # NB: for crew-owned apps the backend carries the crew id in
        # `workflow_id` — opaque to the frontend, but it must be a string.
        "non_nullable": ["workflow_id", "workspace_slug", "app_slug", "title", "mode", "auth_mode", "config"],
    },
    "SessionOut": {
        # workflow_id / crew_id are `.nullable().optional()` in zod —
        # deliberately NOT listed as required here.
        "required": [
            "id",
            "cookie_id",
            "user_id",
            "first_seen_at",
            "last_seen_at",
            "message_count",
            "total_cost_usd",
            "total_tokens",
            "is_blocked",
        ],
        # workflow_id / crew_id / user_id are nullable BY CONTRACT
        # (crew-owned sessions have workflow_id null) — zod matches.
        "non_nullable": [
            "id",
            "cookie_id",
            "first_seen_at",
            "last_seen_at",
            "message_count",
            "total_cost_usd",
            "total_tokens",
            "is_blocked",
        ],
    },
    "MessageOut": {
        "required": [
            "id",
            "session_id",
            "role",
            "content",
            "artifacts",
            "execution_id",
            "tokens",
            "cost_usd",
            "latency_ms",
            "is_error",
            "created_at",
        ],
        "non_nullable": [
            "id",
            "session_id",
            "role",
            "content",
            "artifacts",
            "tokens",
            "cost_usd",
            "latency_ms",
            "is_error",
            "created_at",
        ],
    },
    "SessionEnvelope": {
        "required": ["session", "messages"],
        "non_nullable": ["session", "messages"],
    },
    "SessionListOut": {
        "required": ["sessions"],
        "non_nullable": ["sessions"],
    },
    "SessionSummaryOut": {
        "required": ["id", "title", "message_count", "last_seen_at"],
        "non_nullable": ["id", "title", "message_count", "last_seen_at"],
    },
    "SendMessageOut": {
        "required": ["message_id", "execution_id", "stream_url"],
        "non_nullable": ["message_id", "execution_id", "stream_url"],
    },
}


def _is_nullable(prop_schema: dict) -> bool:
    """True when the OpenAPI property accepts JSON null."""
    if prop_schema.get("nullable"):  # OpenAPI 3.0 style
        return True
    if prop_schema.get("type") == "null":
        return True
    for variant in prop_schema.get("anyOf", []) + prop_schema.get("oneOf", []):
        if variant.get("type") == "null":
            return True
    return False


def main() -> int:
    warnings.filterwarnings("ignore")
    from apps.api.app.main import app

    schemas = app.openapi()["components"]["schemas"]
    problems: list[str] = []

    for name, contract in FRONTEND_CONTRACT.items():
        component = schemas.get(name)
        if component is None:
            problems.append(f"{name}: component vanished from the OpenAPI spec")
            continue
        properties = component.get("properties", {})
        backend_required = set(component.get("required", []))

        for field in contract["required"]:
            if field not in properties:
                problems.append(f"{name}.{field}: frontend requires it; backend no longer has it")
            elif field not in backend_required and "default" not in properties[field]:
                problems.append(
                    f"{name}.{field}: frontend requires it; backend made it optional with no default"
                )
        for field in contract["non_nullable"]:
            if field in properties and _is_nullable(properties[field]):
                problems.append(
                    f"{name}.{field}: frontend types it non-nullable; backend now allows null"
                )

    if problems:
        print("SCHEMA DRIFT — backend response models diverged from the frontend contract:")
        for p in problems:
            print(f"  - {p}")
        print(
            "\nFix the backend model, or update the zod schema in "
            "apps/web/src/features/public-app/types/publicAppTypes.ts "
            "AND this manifest together."
        )
        return 1

    print(f"schema drift check OK — {len(FRONTEND_CONTRACT)} components verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
