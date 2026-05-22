import hashlib
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request, status

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.models.api_key import ApiKey
from apps.api.app.models.user import User
from apps.api.app.repositories.api_key_repository import ApiKeyRepository
from apps.api.app.repositories.user_repository import UserRepository
from apps.api.app.services.api_key_service import ApiKeyService


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_api_key_service_create_key():
    # Arrange
    mock_db = AsyncMock()
    service = ApiKeyService(mock_db)
    user_id = uuid.uuid4()
    key_name = "My Test Key"

    def mock_create(api_key):
        api_key.id = uuid.uuid4()
        return api_key

    service.repo.create = AsyncMock(side_effect=mock_create)

    # Act
    created_key, token_plain = await service.create_key(user_id, key_name)

    # Assert
    assert token_plain.startswith("fuse_live_")
    assert created_key.user_id == user_id
    assert created_key.name == key_name
    assert created_key.key_preview.startswith("fuse_live_")
    assert "..." in created_key.key_preview

    # Verify key_hash corresponds to token
    expected_hash = hashlib.sha256(token_plain.encode()).hexdigest()
    assert created_key.key_hash == expected_hash

    # Repo create should be called
    service.repo.create.assert_called_once()


@pytest.mark.anyio
async def test_api_key_service_revoke_key_success():
    # Arrange
    mock_db = AsyncMock()
    service = ApiKeyService(mock_db)
    user_id = uuid.uuid4()
    key_id = uuid.uuid4()

    mock_key = ApiKey(id=key_id, user_id=user_id, name="Test Key")
    service.repo.get_by_id = AsyncMock(return_value=mock_key)
    service.repo.delete = AsyncMock()

    # Act
    await service.revoke_key(user_id, key_id)

    # Assert
    service.repo.get_by_id.assert_called_once_with(key_id)
    service.repo.delete.assert_called_once_with(mock_key)


@pytest.mark.anyio
async def test_api_key_service_revoke_key_not_found():
    # Arrange
    mock_db = AsyncMock()
    service = ApiKeyService(mock_db)
    user_id = uuid.uuid4()
    key_id = uuid.uuid4()

    service.repo.get_by_id = AsyncMock(return_value=None)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.revoke_key(user_id, key_id)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "API Key not found"


@pytest.mark.anyio
async def test_api_key_service_revoke_key_wrong_user():
    # Arrange
    mock_db = AsyncMock()
    service = ApiKeyService(mock_db)
    owner_id = uuid.uuid4()
    attacker_id = uuid.uuid4()
    key_id = uuid.uuid4()

    mock_key = ApiKey(id=key_id, user_id=owner_id, name="Test Key")
    service.repo.get_by_id = AsyncMock(return_value=mock_key)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.revoke_key(attacker_id, key_id)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "API Key not found"


@pytest.mark.anyio
async def test_get_current_user_with_x_api_key():
    # Arrange
    mock_db = AsyncMock()
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, email="dev@fuse.com", is_active=True)
    mock_key_record = ApiKey(user_id=user_id, name="Token Name")

    # Mock DB interaction
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.side_effect = [mock_key_record, mock_user]
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Construct request with custom header
    request = Request(
        scope={
            "type": "http",
            "headers": [(b"x-api-key", b"fuse_live_test_api_key")],
        }
    )

    with (
        patch.object(ApiKeyRepository, "get_by_hash", return_value=mock_key_record) as mock_get_hash,
        patch.object(UserRepository, "get_by_id", return_value=mock_user) as mock_get_user,
    ):
        # Act
        authenticated_user = await get_current_user(request=request, db=mock_db, token=None)

        # Assert
        assert authenticated_user == mock_user
        expected_hash = hashlib.sha256(b"fuse_live_test_api_key").hexdigest()
        mock_get_hash.assert_called_once_with(expected_hash)
        mock_get_user.assert_called_once_with(user_id)


@pytest.mark.anyio
async def test_get_current_user_with_bearer_api_key():
    # Arrange
    mock_db = AsyncMock()
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, email="dev@fuse.com", is_active=True)
    mock_key_record = ApiKey(user_id=user_id, name="Token Name")

    # Construct request with Bearer authorization
    request = Request(
        scope={
            "type": "http",
            "headers": [(b"authorization", b"Bearer fuse_live_token_string")],
        }
    )

    with (
        patch.object(ApiKeyRepository, "get_by_hash", return_value=mock_key_record),
        patch.object(UserRepository, "get_by_id", return_value=mock_user),
    ):
        # Act
        authenticated_user = await get_current_user(
            request=request, db=mock_db, token="fuse_live_token_string"
        )

        # Assert
        assert authenticated_user == mock_user


@pytest.mark.anyio
async def test_get_current_user_with_invalid_api_key_raises_401():
    # Arrange
    mock_db = AsyncMock()

    # Construct request with invalid Key
    request = Request(
        scope={
            "type": "http",
            "headers": [(b"x-api-key", b"fuse_live_invalid_key")],
        }
    )

    with patch.object(ApiKeyRepository, "get_by_hash", return_value=None):
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request=request, db=mock_db, token=None)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"
