"""Comprehensive tests for auth middleware."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient

from app.core.auth.keycloak import (
    KeycloakUser,
    get_current_user,
    get_current_user_optional,
    require_role,
    security,
)

# Alias get_current_user as get_current_user_required for tests
get_current_user_required = get_current_user
from app.core.middleware.auth_middleware import (
    add_auth_middleware,
    get_current_user_optional_from_request,
)


class TestSecurityScheme:
    """Test security scheme configuration."""

    def test_security_scheme_creation(self) -> None:
        """Test HTTPBearer security scheme creation."""
        assert isinstance(security, HTTPBearer)
        assert security.auto_error is False

    def test_security_scheme_attributes(self) -> None:
        """Test security scheme attributes."""
        assert hasattr(security, "scheme_name")
        assert hasattr(security, "model")


class TestGetCurrentUserOptional:
    """Test optional user authentication."""

    @pytest.mark.asyncio
    async def test_get_current_user_optional_no_credentials(self) -> None:
        """Test get_current_user_optional with no credentials."""
        result = await get_current_user_optional(credentials=None)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_optional_with_valid_credentials(self) -> None:
        """Test get_current_user_optional with valid credentials."""
        MagicMock()
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid-token"

        mock_user = KeycloakUser(
            sub="test-user-id",
            preferred_username="testuser",
            email="test@example.com",
            roles=["user"],
        )

        with patch("app.core.auth.keycloak.keycloak_service") as mock_service:
            mock_service.get_user_info = AsyncMock(return_value=mock_user)

            result = await get_current_user_optional(credentials=mock_credentials)

            assert result == mock_user
            mock_service.get_user_info.assert_called_once_with("valid-token")

    @pytest.mark.asyncio
    async def test_get_current_user_optional_with_invalid_credentials(self) -> None:
        """Test get_current_user_optional with invalid credentials."""
        MagicMock()
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid-token"

        with patch("app.core.auth.keycloak.keycloak_service") as mock_service:
            mock_service.get_user_info = AsyncMock(
                side_effect=Exception("Invalid token")
            )

            result = await get_current_user_optional(credentials=mock_credentials)

            assert result is None
            mock_service.get_user_info.assert_called_once_with("invalid-token")


class TestGetCurrentUserOptionalFromRequest:
    """Test optional user authentication from request."""

    @pytest.mark.asyncio
    async def test_get_current_user_optional_from_request_no_auth_header(self) -> None:
        """Test get_current_user_optional_from_request with no auth header."""
        mock_request = MagicMock()
        mock_request.headers = {}

        result = await get_current_user_optional_from_request(mock_request)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_optional_from_request_invalid_auth_header(
        self,
    ) -> None:
        """Test get_current_user_optional_from_request with invalid auth header."""
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Invalid"}

        result = await get_current_user_optional_from_request(mock_request)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_optional_from_request_valid_auth_header(
        self,
    ) -> None:
        """Test get_current_user_optional_from_request with valid auth header."""
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer valid-token"}

        mock_user = KeycloakUser(
            sub="test-user-id",
            preferred_username="testuser",
            email="test@example.com",
            roles=["user"],
        )

        with patch(
            "app.core.middleware.auth_middleware.keycloak_service"
        ) as mock_service:
            mock_service.get_user_info = AsyncMock(return_value=mock_user)

            result = await get_current_user_optional_from_request(mock_request)

            assert result == mock_user
            mock_service.get_user_info.assert_called_once_with("valid-token")

    @pytest.mark.asyncio
    async def test_get_current_user_optional_from_request_invalid_token(self) -> None:
        """Test get_current_user_optional_from_request with invalid token."""
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer invalid-token"}

        with patch(
            "app.core.middleware.auth_middleware.keycloak_service"
        ) as mock_service:
            mock_service.get_user_info = AsyncMock(
                side_effect=Exception("Invalid token")
            )

            result = await get_current_user_optional_from_request(mock_request)

            assert result is None
            mock_service.get_user_info.assert_called_once_with("invalid-token")


class TestGetCurrentUserRequired:
    """Test required user authentication."""

    @pytest.mark.asyncio
    async def test_get_current_user_required_with_valid_credentials(self) -> None:
        """Test get_current_user_required with valid credentials."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid-token"

        mock_user = KeycloakUser(
            sub="test-user-id",
            preferred_username="testuser",
            email="test@example.com",
            roles=["user"],
        )

        with patch("app.core.auth.keycloak.keycloak_service") as mock_service:
            mock_service.get_user_info = AsyncMock(return_value=mock_user)

            result = await get_current_user_required(credentials=mock_credentials)

            assert result == mock_user
            mock_service.get_user_info.assert_called_once_with("valid-token")

    @pytest.mark.asyncio
    async def test_get_current_user_required_with_invalid_credentials(self) -> None:
        """Test get_current_user_required with invalid credentials."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid-token"

        with patch("app.core.auth.keycloak.keycloak_service") as mock_service:
            mock_service.get_user_info = AsyncMock(
                side_effect=Exception("Invalid token")
            )

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_required(credentials=mock_credentials)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc_info.value.detail == "Invalid authentication credentials"
            assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}
            mock_service.get_user_info.assert_called_once_with("invalid-token")


class TestRequireRole:
    """Test role-based authorization."""

    @pytest.mark.asyncio
    async def test_require_role_with_valid_role(self) -> None:
        """Test require_role with user having required role."""
        mock_user = KeycloakUser(
            sub="test-user-id",
            preferred_username="testuser",
            email="test@example.com",
            roles=["admin", "user"],
        )

        with patch("app.core.auth.keycloak.keycloak_service") as mock_service:
            mock_service.check_role = AsyncMock(return_value=True)

            role_checker = require_role("admin")
            result = await role_checker(mock_user)

            assert result == mock_user
            mock_service.check_role.assert_called_once_with(mock_user, "admin")

    @pytest.mark.asyncio
    async def test_require_role_with_invalid_role(self) -> None:
        """Test require_role with user not having required role."""
        mock_user = KeycloakUser(
            sub="test-user-id",
            preferred_username="testuser",
            email="test@example.com",
            roles=["user"],
        )

        with patch("app.core.auth.keycloak.keycloak_service") as mock_service:
            mock_service.check_role = AsyncMock(return_value=False)

            role_checker = require_role("admin")

            with pytest.raises(HTTPException) as exc_info:
                await role_checker(mock_user)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert exc_info.value.detail == "Role 'admin' required"
            mock_service.check_role.assert_called_once_with(mock_user, "admin")

    @pytest.mark.asyncio
    async def test_require_role_dependency_injection(self) -> None:
        """Test require_role as FastAPI dependency."""
        mock_user = KeycloakUser(
            sub="test-user-id",
            preferred_username="testuser",
            email="test@example.com",
            roles=["admin"],
        )

        with patch("app.core.auth.keycloak.keycloak_service") as mock_service:
            mock_service.check_role = AsyncMock(return_value=True)

            role_checker = require_role("admin")

            # Simulate FastAPI dependency injection
            result = await role_checker(mock_user)

            assert result == mock_user
            mock_service.check_role.assert_called_once_with(mock_user, "admin")


class TestAddAuthMiddleware:
    """Test auth middleware integration."""

    def test_add_auth_middleware_returns_none(self) -> None:
        """Test add_auth_middleware returns None."""
        app = FastAPI()
        result = add_auth_middleware(app)
        assert result is None

    def test_add_auth_middleware_adds_middleware(self) -> None:
        """Test add_auth_middleware adds middleware to app."""
        app = FastAPI()

        # Count middleware before
        middleware_count_before = len(app.user_middleware)

        add_auth_middleware(app)

        # Count middleware after
        middleware_count_after = len(app.user_middleware)

        assert middleware_count_after > middleware_count_before

    @pytest.mark.asyncio
    async def test_auth_middleware_with_authenticated_request(self) -> None:
        """Test auth middleware with authenticated request."""
        app = FastAPI()
        add_auth_middleware(app)

        @app.get("/test")
        async def test_endpoint(request: Request):
            return {"user": request.state.user.sub if request.state.user else None}

        mock_user = KeycloakUser(
            sub="test-user-id",
            preferred_username="testuser",
            email="test@example.com",
            roles=["user"],
        )

        with patch(
            "app.core.middleware.auth_middleware.keycloak_service"
        ) as mock_service:
            mock_service.get_user_info = AsyncMock(return_value=mock_user)

            client = TestClient(app)
            response = client.get(
                "/test", headers={"Authorization": "Bearer valid-token"}
            )

            assert response.status_code == 200
            assert response.json()["user"] == "test-user-id"

    @pytest.mark.asyncio
    async def test_auth_middleware_with_unauthenticated_request(self) -> None:
        """Test auth middleware with unauthenticated request."""
        app = FastAPI()
        add_auth_middleware(app)

        @app.get("/test")
        async def test_endpoint(request: Request):
            return {"user": request.state.user.sub if request.state.user else None}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        assert response.json()["user"] is None

    @pytest.mark.asyncio
    async def test_auth_middleware_with_invalid_token(self) -> None:
        """Test auth middleware with invalid token."""
        app = FastAPI()
        add_auth_middleware(app)

        @app.get("/test")
        async def test_endpoint(request: Request):
            return {"user": request.state.user.sub if request.state.user else None}

        with patch(
            "app.core.middleware.auth_middleware.keycloak_service"
        ) as mock_service:
            mock_service.get_user_info = AsyncMock(
                side_effect=Exception("Invalid token")
            )

            client = TestClient(app)
            response = client.get(
                "/test", headers={"Authorization": "Bearer invalid-token"}
            )

            assert response.status_code == 200
            assert response.json()["user"] is None


class TestAuthMiddlewareIntegration:
    """Integration tests for auth middleware."""

    @pytest.mark.asyncio
    async def test_full_auth_flow_with_middleware(self) -> None:
        """Test complete authentication flow with middleware."""
        app = FastAPI()
        add_auth_middleware(app)

        @app.get("/public")
        async def public_endpoint(request: Request):
            return {"user": request.state.user.sub if request.state.user else None}

        @app.get("/protected")
        async def protected_endpoint(
            current_user: KeycloakUser = Depends(get_current_user_required),
        ):
            return {"user": current_user.sub}

        @app.get("/admin")
        async def admin_endpoint(
            current_user: KeycloakUser = Depends(require_role("admin")),
        ):
            return {"user": current_user.sub, "role": "admin"}

        mock_user = KeycloakUser(
            sub="test-user-id",
            preferred_username="testuser",
            email="test@example.com",
            roles=["admin", "user"],
        )

        with (
            patch("jwt.decode") as mock_jwt_decode,
            patch("jwt.PyJWKClient") as mock_jwks_client,
            patch("app.core.auth.keycloak.keycloak_service") as mock_service,
        ):
            # Mock JWT decoding
            mock_jwt_decode.return_value = {
                "sub": "test-user-id",
                "email": "test@example.com",
                "name": "Test User",
                "preferred_username": "testuser",
                "realm_access": {"roles": ["admin", "user"]},
            }
            mock_signing_key = MagicMock()
            mock_signing_key.key = "mock-key"
            mock_jwks_client.return_value.get_signing_key_from_jwt.return_value = (
                mock_signing_key
            )

            # Mock service methods
            mock_service.get_user_info = AsyncMock(return_value=mock_user)
            mock_service.check_role = AsyncMock(return_value=True)

            client = TestClient(app)

            # Test public endpoint (no auth required)
            response = client.get("/public")
            assert response.status_code == 200
            assert response.json()["user"] is None

            # Test public endpoint with auth
            response = client.get(
                "/public", headers={"Authorization": "Bearer valid-token"}
            )
            assert response.status_code == 200
            assert response.json()["user"] == "test-user-id"

            # Test protected endpoint
            response = client.get(
                "/protected", headers={"Authorization": "Bearer valid-token"}
            )
            assert response.status_code == 200
            assert response.json()["user"] == "test-user-id"

            # Test admin endpoint
            response = client.get(
                "/admin", headers={"Authorization": "Bearer valid-token"}
            )
            assert response.status_code == 200
            assert response.json()["user"] == "test-user-id"
            assert response.json()["role"] == "admin"

    @pytest.mark.asyncio
    async def test_auth_middleware_error_handling(self) -> None:
        """Test auth middleware error handling."""
        app = FastAPI()
        add_auth_middleware(app)

        @app.get("/test")
        async def test_endpoint(request: Request):
            return {"user": request.state.user.sub if request.state.user else None}

        # Test with malformed auth header
        client = TestClient(app)
        response = client.get("/test", headers={"Authorization": "Invalid Format"})

        assert response.status_code == 200
        assert response.json()["user"] is None

        # Test with empty auth header
        response = client.get("/test", headers={"Authorization": ""})

        assert response.status_code == 200
        assert response.json()["user"] is None

    @pytest.mark.asyncio
    async def test_auth_middleware_with_different_token_formats(self) -> None:
        """Test auth middleware with different token formats."""
        app = FastAPI()
        add_auth_middleware(app)

        @app.get("/test")
        async def test_endpoint(request: Request):
            return {"user": request.state.user.sub if request.state.user else None}

        mock_user = KeycloakUser(
            sub="test-user-id",
            preferred_username="testuser",
            email="test@example.com",
            roles=["user"],
        )

        with patch(
            "app.core.middleware.auth_middleware.keycloak_service"
        ) as mock_service:
            mock_service.get_user_info = AsyncMock(return_value=mock_user)

            client = TestClient(app)

            # Test with Bearer token (case-sensitive)
            response = client.get(
                "/test", headers={"Authorization": "Bearer valid-token"}
            )
            assert response.status_code == 200
            assert response.json()["user"] == "test-user-id"

            # Test with lowercase bearer (should not work - case-sensitive)
            response = client.get(
                "/test", headers={"Authorization": "bearer valid-token"}
            )
            assert response.status_code == 200
            assert (
                response.json()["user"] is None
            )  # Case-sensitive, so lowercase doesn't work

            # Test with extra spaces (should work - just removes "Bearer " prefix)
            response = client.get(
                "/test", headers={"Authorization": "Bearer  valid-token  "}
            )
            assert response.status_code == 200
            assert response.json()["user"] == "test-user-id"
