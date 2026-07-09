"""Shared helper for DB nodes: resolve a workspace credential dict.

Every DB node (postgres, mysql, mongodb, neo4j) has the same
credential-fetch flow — pull the row by id, decrypt via
`CredentialService`. Keep it in one place so each node stays a thin
lookup layer.
"""

from __future__ import annotations

import uuid
from typing import Any


async def resolve_credential(cred_id: str, workspace_id: Any) -> dict[str, Any] | None:
    """Return the decrypted credential dict for `cred_id`, or None."""
    if not cred_id:
        return None
    from apps.api.app.core.database import AsyncSessionLocal
    from apps.api.app.features.credentials.service import CredentialService

    async with AsyncSessionLocal() as db:
        service = CredentialService(db)
        cred_row = await service.repo.get_by_id_and_workspace(uuid.UUID(cred_id), workspace_id)
        if cred_row is None:
            return None
        data = await service.get_decrypted_credential(cred_row)
    return data if isinstance(data, dict) else None
