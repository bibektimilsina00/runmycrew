import json
from typing import Any, cast

from sqlalchemy import select

from apps.api.app.core.database import AsyncSessionLocal
from apps.api.app.features.credentials.manager.encryption.aes import encryption_service
from apps.api.app.features.credentials.models import Credential


class CredentialVault:
    async def get_decrypted_credential(self, credential_id: str) -> dict[str, Any]:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Credential).where(Credential.id == credential_id))
            credential = result.scalar_one_or_none()

            if not credential:
                raise ValueError("Credential not found")

            decrypted_json = encryption_service.decrypt(cast(str, credential.encrypted_data))
            return json.loads(decrypted_json)

    async def store_credential(
        self, name: str, type: str, data: dict[str, Any], metadata: dict[str, Any] | None = None
    ):
        async with AsyncSessionLocal() as db:
            encrypted_data = encryption_service.encrypt(json.dumps(data))
            new_cred = Credential(
                name=name, type=type, encrypted_data=encrypted_data, meta=metadata
            )
            db.add(new_cred)
            await db.commit()
            await db.refresh(new_cred)
            return new_cred


credential_vault = CredentialVault()
