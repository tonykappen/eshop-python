"""Tests for Keycloak authentication module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status

from app.core.auth.keycloak import (
    KeycloakService,
    KeycloakUser,
    add_keycloak_routes,
    get_current_user,
    get_current_user_optional,
    get_keycloak_app,
    keycloak_service,
    require_role,
    security,
)


class TestKeycloakUser:
    """Test KeycloakUser model."""

    def test_keycloak_user_creation(self) -> None:
        """Test creating a KeycloakUser with all fields."""
        user = KeycloakUser(
            sub="user123",
            email="test@example.com",
            name="Test User",
            preferred_username="testuser",
            roles=["user", "admin"],
        )
        assert user.sub == "user123"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.preferred_username == "testuser"
        assert user.roles == ["user", "admin"]

    def test_keycloak_user_creation_minimal(self) -> None:
        """Test creating a KeycloakUser with minimal fields."""
        user = KeycloakUser(sub="user123")
        assert user.sub == "user123"
        assert user.email is None
        assert user.name is None
        assert user.preferred_username is None
        assert user.roles == []

    def test_keycloak_user_serialization(self) -> None:
        """Test KeycloakUser serialization."""
        user = KeycloakUser(sub="user123", email="test@example.com", roles=["user"])
        user_dict = user.model_dump()
        assert user_dict["sub"] == "user123"
        assert user_dict["email"] == "test@example.com"
        assert user_dict["roles"] == ["user"]

    def test_keycloak_user_equality(self) -> None:
        """Test KeycloakUser equality."""
        user1 = KeycloakUser(sub="user123", email="test@example.com")
        user2 = KeycloakUser(sub="user123", email="test@example.com")
        user3 = KeycloakUser(sub="user456", email="test@example.com")

        assert user1 == user2
        assert user1 != user3

    def test_keycloak_user_copy(self) -> None:
        """Test KeycloakUser copying."""
        user = KeycloakUser(sub="user123", email="test@example.com")
        user_copy = user.model_copy(update={"email": "new@example.com"})

        assert user_copy.sub == "user123"
        assert user_copy.email == "new@example.com"
        assert user.email == "test@example.com"  # Original unchanged


class TestKeycloakService:
    """Test KeycloakService class."""

    def test_keycloak_service_initialization(self) -> None:
        """Test KeycloakService initialization."""
        service = KeycloakService()
        assert service.keycloak is None
        assert service._initialized is False

    @patch("app.core.auth.keycloak.FastAPIKeycloak")
    @patch("app.core.auth.keycloak.settings")
    def test_initialize_keycloak_success(
        self, _mock_settings: MagicMock, mock_fastapi_keycloak: MagicMock
    ) -> None:
        """Test successful Keycloak initialization."""
        _mock_settings.keycloak_server_url = "http://localhost:8080"
        _mock_settings.keycloak_client_id = "test-client"
        _mock_settings.keycloak_client_secret = "test-secret"
        _mock_settings.keycloak_realm = "test-realm"
        _mock_settings.keycloak_callback_uri = "http://localhost:8000/callback"

        mock_keycloak_instance = MagicMock()
        mock_fastapi_keycloak.return_value = mock_keycloak_instance

        service = KeycloakService()
        service._initialize_keycloak()

        assert service._initialized is True
        assert service.keycloak == mock_keycloak_instance
        mock_fastapi_keycloak.assert_called_once_with(
            server_url="http://localhost:8080",
            client_id="test-client",
            client_secret="test-secret",
            realm="test-realm",
            callback_uri="http://localhost:8000/callback",
            admin_client_secret=None,
        )

    @patch("app.core.auth.keycloak.FastAPIKeycloak")
    @patch("app.core.auth.keycloak.settings")
    def test_initialize_keycloak_failure(
        self, _mock_settings: MagicMock, mock_fastapi_keycloak: MagicMock
    ) -> None:
        """Test Keycloak initialization failure."""
        mock_fastapi_keycloak.side_effect = Exception("Connection failed")

        service = KeycloakService()
        service._initialize_keycloak()

        # In failure case, _initialized remains False and keycloak is None
        assert service._initialized is False
        assert service.keycloak is None

    @patch("app.core.auth.keycloak.FastAPIKeycloak")
    @patch("app.core.auth.keycloak.settings")
    def test_initialize_keycloak_idempotent(
        self, _mock_settings: MagicMock, mock_fastapi_keycloak: MagicMock
    ) -> None:
        """Test that initialization is idempotent."""
        mock_keycloak_instance = MagicMock()
        mock_fastapi_keycloak.return_value = mock_keycloak_instance

        service = KeycloakService()
        service._initialize_keycloak()
        service._initialize_keycloak()  # Second call should not reinitialize

        mock_fastapi_keycloak.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_token_success(self) -> None:
        """Test successful token verification."""
        expected_token_info = {
            "sub": "user123",
            "email": "test@example.com",
            "name": "Test User",
        }

        with patch("jwt.decode") as mock_jwt_decode, \
             patch("jwt.PyJWKClient") as mock_jwks_client:
            
            # Mock the JWT decoding process
            mock_jwt_decode.return_value = expected_token_info
            mock_signing_key = MagicMock()
            mock_signing_key.key = "mock-key"
            mock_jwks_client.return_value.get_signing_key_from_jwt.return_value = mock_signing_key

            service = KeycloakService()
            result = await service.verify_token("valid-token")

            assert result["sub"] == "user123"
            assert result["email"] == "test@example.com"
            assert result["name"] == "Test User"
            mock_jwt_decode.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_token_not_initialized(self) -> None:
        """Test token verification when Keycloak is not initialized."""
        service = KeycloakService()
        service.keycloak = None
        service._initialized = True

        with pytest.raises(HTTPException) as exc_info:
            await service.verify_token("token")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid token"

    @pytest.mark.asyncio
    async def test_verify_token_failure(self) -> None:
        """Test token verification failure."""
        mock_keycloak = MagicMock()
        mock_keycloak.decode_token.side_effect = Exception("Invalid token")

        service = KeycloakService()
        service.keycloak = mock_keycloak  # type: ignore
        service._initialized = True

        with pytest.raises(HTTPException) as exc_info:
            await service.verify_token("invalid-token")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid token"

    @pytest.mark.asyncio
    async def test_get_user_info_success(self) -> None:
        """Test successful user info retrieval."""
        expected_token_info = {
            "sub": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "preferred_username": "testuser",
            "realm_access": {"roles": ["user", "admin"]},
        }

        with patch("jwt.decode") as mock_jwt_decode, \
             patch("jwt.PyJWKClient") as mock_jwks_client:
            
            # Mock the JWT decoding process
            mock_jwt_decode.return_value = expected_token_info
            mock_signing_key = MagicMock()
            mock_signing_key.key = "mock-key"
            mock_jwks_client.return_value.get_signing_key_from_jwt.return_value = mock_signing_key

            service = KeycloakService()
            user = await service.get_user_info("valid-token")

            assert isinstance(user, KeycloakUser)
            assert user.sub == "user123"
            assert user.email == "test@example.com"
            assert user.name == "Test User"
            assert user.preferred_username == "testuser"
            assert user.roles == ["user", "admin"]

    @pytest.mark.asyncio
    async def test_get_user_info_minimal_token(self) -> None:
        """Test user info retrieval with minimal token data."""
        expected_token_info = {"sub": "user123"}

        with patch("jwt.decode") as mock_jwt_decode, \
             patch("jwt.PyJWKClient") as mock_jwks_client:
            
            # Mock the JWT decoding process
            mock_jwt_decode.return_value = expected_token_info
            mock_signing_key = MagicMock()
            mock_signing_key.key = "mock-key"
            mock_jwks_client.return_value.get_signing_key_from_jwt.return_value = mock_signing_key

            service = KeycloakService()
            user = await service.get_user_info("valid-token")

            assert isinstance(user, KeycloakUser)
            assert user.sub == "user123"
            assert user.email is None
            assert user.name is None
            assert user.preferred_username is None
            assert user.roles == []

    @pytest.mark.asyncio
    async def test_check_role_user_has_role(self) -> None:
        """Test role checking when user has the required role."""
        user = KeycloakUser(sub="user123", roles=["user", "admin"])
        service = KeycloakService()

        result = await service.check_role(user, "admin")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_role_user_does_not_have_role(self) -> None:
        """Test role checking when user doesn't have the required role."""
        user = KeycloakUser(sub="user123", roles=["user"])
        service = KeycloakService()

        result = await service.check_role(user, "admin")
        assert result is False

    @pytest.mark.asyncio
    async def test_check_role_empty_roles(self) -> None:
        """Test role checking with empty roles list."""
        user = KeycloakUser(sub="user123", roles=[])
        service = KeycloakService()

        result = await service.check_role(user, "admin")
        assert result is False

    @patch("httpx.AsyncClient")
    @patch("app.core.auth.keycloak.settings")
    @pytest.mark.asyncio
    async def test_health_check_success(
        self, mock_settings: MagicMock, mock_async_client: MagicMock
    ) -> None:
        """Test successful health check."""
        mock_settings.keycloak_server_url = "http://localhost:8080"
        mock_settings.keycloak_realm = "test-realm"

        mock_response = AsyncMock()
        mock_response.status_code = 200

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_async_client.return_value = mock_client_instance

        service = KeycloakService()
        result = await service.health_check()

        assert result["status"] == "healthy"
        assert result["service"] == "keycloak"
        assert result["realm"] == "test-realm"
        assert result["server_url"] == "http://localhost:8080"
        assert result["response_time"] == "OK"

    @patch("httpx.AsyncClient")
    @patch("app.core.auth.keycloak.settings")
    @pytest.mark.asyncio
    async def test_health_check_failure(
        self, mock_settings: MagicMock, mock_async_client: MagicMock
    ) -> None:
        """Test health check failure."""
        mock_settings.keycloak_server_url = "http://localhost:8080"
        mock_settings.keycloak_realm = "test-realm"

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get.side_effect = Exception("Connection failed")
        mock_async_client.return_value = mock_client_instance

        service = KeycloakService()
        result = await service.health_check()

        assert result["status"] == "unhealthy"
        assert result["service"] == "keycloak"
        assert "Connection failed" in result["error"]

    @patch("app.core.auth.keycloak.FastAPIKeycloak")
    @patch("app.core.auth.keycloak.settings")
    def test_get_current_user_dependency_success(
        self, _mock_settings: MagicMock, mock_fastapi_keycloak: MagicMock
    ) -> None:
        """Test successful dependency creation."""
        mock_keycloak_instance = MagicMock()
        mock_dependency = MagicMock()
        mock_keycloak_instance.get_current_user.return_value = mock_dependency
        mock_fastapi_keycloak.return_value = mock_keycloak_instance

        service = KeycloakService()
        service.keycloak = mock_keycloak_instance  # type: ignore
        service._initialized = True

        result = service.get_current_user_dependency()
        assert result == mock_dependency

    @patch("app.core.auth.keycloak.FastAPIKeycloak")
    @patch("app.core.auth.keycloak.settings")
    def test_get_current_user_dependency_not_initialized(
        self, _mock_settings: MagicMock, _mock_fastapi_keycloak: MagicMock
    ) -> None:
        """Test dependency creation when Keycloak is not initialized."""
        service = KeycloakService()
        service.keycloak = None
        service._initialized = True

        with pytest.raises(Exception, match="Keycloak not initialized"):
            service.get_current_user_dependency()

    @patch("app.core.auth.keycloak.FastAPIKeycloak")
    @patch("app.core.auth.keycloak.settings")
    def test_require_role_dependency_success(
        self, _mock_settings: MagicMock, mock_fastapi_keycloak: MagicMock
    ) -> None:
        """Test successful role dependency creation."""
        mock_keycloak_instance = MagicMock()
        mock_dependency = MagicMock()
        mock_keycloak_instance.require_roles.return_value = mock_dependency
        mock_fastapi_keycloak.return_value = mock_keycloak_instance

        service = KeycloakService()
        service.keycloak = mock_keycloak_instance  # type: ignore
        service._initialized = True

        result = service.require_role_dependency("admin")
        assert result == mock_dependency
        mock_keycloak_instance.require_roles.assert_called_once_with("admin")


class TestAuthDependencies:
    """Test authentication dependencies."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self) -> None:
        """Test successful current user retrieval."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid-token"

        mock_user = KeycloakUser(sub="user123", email="test@example.com")

        with patch.object(keycloak_service, "get_user_info", return_value=mock_user):
            result = await get_current_user(mock_credentials)

            assert result == mock_user
            keycloak_service.get_user_info.assert_called_once_with("valid-token")  # type: ignore

    @pytest.mark.asyncio
    async def test_get_current_user_optional_with_credentials(self) -> None:
        """Test optional current user with valid credentials."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid-token"

        mock_user = KeycloakUser(sub="user123", email="test@example.com")

        with patch.object(keycloak_service, "get_user_info", return_value=mock_user):
            result = await get_current_user_optional(mock_credentials)

            assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_current_user_optional_no_credentials(self) -> None:
        """Test optional current user without credentials."""
        result = await get_current_user_optional(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_optional_auth_failure(self) -> None:
        """Test optional current user with authentication failure."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid-token"

        with patch.object(
            keycloak_service, "get_user_info", side_effect=Exception("Auth failed")
        ):
            result = await get_current_user_optional(mock_credentials)

            assert result is None

    def test_require_role_decorator(self) -> None:
        """Test require_role decorator."""
        role_checker = require_role("admin")
        assert callable(role_checker)

    @pytest.mark.asyncio
    async def test_require_role_success(self) -> None:
        """Test require_role with user having required role."""
        mock_user = KeycloakUser(sub="user123", roles=["admin"])

        with (
            patch("app.core.auth.keycloak.get_current_user", return_value=mock_user),
            patch.object(keycloak_service, "check_role", AsyncMock(return_value=True)),
        ):
            role_checker = require_role("admin")
            result = await role_checker(mock_user)  # type: ignore

            assert result == mock_user

    @pytest.mark.asyncio
    async def test_require_role_failure(self) -> None:
        """Test require_role with user not having required role."""
        mock_user = KeycloakUser(sub="user123", roles=["user"])

        with (
            patch("app.core.auth.keycloak.get_current_user", return_value=mock_user),
            patch.object(keycloak_service, "check_role", AsyncMock(return_value=False)),
        ):
            role_checker = require_role("admin")

            with pytest.raises(HTTPException) as exc_info:
                await role_checker(mock_user)  # type: ignore

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert exc_info.value.detail == "Role 'admin' required"


class TestKeycloakIntegration:
    """Test Keycloak integration helpers."""

    @patch("app.core.auth.keycloak.keycloak_service")
    def test_get_keycloak_app_success(self, mock_keycloak_service: MagicMock) -> None:
        """Test successful Keycloak app retrieval."""
        mock_app = MagicMock()
        mock_keycloak_service.keycloak = mock_app

        result = get_keycloak_app()

        assert result == mock_app
        mock_keycloak_service._initialize_keycloak.assert_called_once()

    @patch("app.core.auth.keycloak.keycloak_service")
    def test_add_keycloak_routes_success(
        self, mock_keycloak_service: MagicMock
    ) -> None:
        """Test successful Keycloak routes addition."""
        mock_app = MagicMock()
        mock_keycloak_app = MagicMock()
        mock_keycloak_service.keycloak = mock_keycloak_app

        result = add_keycloak_routes(mock_app)

        assert result == mock_app
        mock_keycloak_service._initialize_keycloak.assert_called_once()
        mock_keycloak_app.add_auth_routes.assert_called_once_with(mock_app)

    @patch("app.core.auth.keycloak.keycloak_service")
    def test_add_keycloak_routes_no_keycloak(
        self, mock_keycloak_service: MagicMock
    ) -> None:
        """Test Keycloak routes addition when Keycloak is not available."""
        mock_app = MagicMock()
        mock_keycloak_service.keycloak = None

        result = add_keycloak_routes(mock_app)

        assert result == mock_app
        mock_keycloak_service._initialize_keycloak.assert_called_once()


class TestSecurityScheme:
    """Test security scheme configuration."""

    def test_security_scheme_configuration(self) -> None:
        """Test security scheme is properly configured."""
        assert security.auto_error is False
        assert hasattr(security, "scheme_name")
        assert hasattr(security, "model")
