import base64
import hashlib

from cryptography.fernet import Fernet

from apps.api.app.core.config import settings


class AESEncryptionService:
    def __init__(self, key: str | None = None):
        raw_key = key or settings.ENCRYPTION_KEY

        if not raw_key:
            from apps.api.app.core.logger import logger

            logger.warning(
                "ENCRYPTION_KEY missing — generating ephemeral key. WARNING: API and Worker will not share credentials!"
            )
            self.fernet = Fernet(Fernet.generate_key())
            return

        try:
            # If it's already a valid Fernet key (44 chars, base64)
            if len(raw_key) == 44:
                self.fernet = Fernet(raw_key.encode())
            else:
                # If it's a hex string (like 64 chars from openssl rand -hex 32)
                # or any other string, hash it to get a consistent 32-byte key
                key_hash = hashlib.sha256(raw_key.encode()).digest()
                fernet_key = base64.urlsafe_b64encode(key_hash)
                self.fernet = Fernet(fernet_key)
        except Exception as e:
            from apps.api.app.core.logger import logger

            logger.error(f"Invalid ENCRYPTION_KEY format: {e}. Falling back to ephemeral key.")
            self.fernet = Fernet(Fernet.generate_key())

    def encrypt(self, data: str) -> str:
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, token: str) -> str:
        return self.fernet.decrypt(token.encode()).decode()


encryption_service = AESEncryptionService()
