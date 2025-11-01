"""Comprehensive tests for auth proxy endpoints with schema validation."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api import auth_proxy
from app.api.auth_proxy import TokenResponse, router
from app.main import app

# Include auth proxy router if not already included
if "/auth-proxy" not in [r.path for r in app.routes]:
    app.include_router(router, prefix="/api/v1")


class TestTokenResponseSchema:
    """Test TokenResponse schema validation."""

    def test_token_response_valid_schema(self):
        """Test TokenResponse with valid data."""
        response = TokenResponse(
            access_token="test-token",
            expires_in=3600,
            refresh_expires_in=7200,
            refresh_token="refresh-token",
            token_type="Bearer",
            scope="openid profile",
        )
        assert response.access_token == "test-token"
        assert response.expires_in == 3600
        assert response.refresh_expires_in == 7200
        assert response.refresh_token == "refresh-token"
        assert response.token_type == "Bearer"
        assert response.scope == "openid profile"

    def test_token_response_missing_required_fields(self):
        """Test TokenResponse validation with missing required fields."""
        with pytest.raises(Exception):  # Pydantic validation error
            TokenResponse(
                access_token="test-token",
                # Missing other required fields
            )

    def test_token_response_type_coercion(self):
        """Test TokenResponse handles type coercion correctly."""
        response = TokenResponse(
            access_token="test-token",
            expires_in="3600",  # String should be converted
            refresh_expires_in="7200",
            refresh_token="refresh-token",
            token_type="Bearer",
            scope="openid",
        )
        assert isinstance(response.expires_in, int)


class TestProxyTokenRequest:
    """Test proxy_token_request endpoint."""

    @pytest.mark.asyncio
    async def test_proxy_token_request_success(self):
        """Test successful token proxy request."""
        mock_token_data = {
            "access_token": "test-access-token",
            "expires_in": 3600,
            "refresh_expires_in": 7200,
            "refresh_token": "test-refresh-token",
            "token_type": "Bearer",
            "scope": "openid profile",
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_token_data
        mock_response.headers = {"content-type": "application/json"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            result = await auth_proxy.proxy_token_request(
                username="testuser",
                password="testpass",
                grant_type="password",
                client_id="test-client",
                client_secret="test-secret",
            )

            assert isinstance(result, TokenResponse)
            assert result.access_token == "test-access-token"
            assert result.expires_in == 3600

            # Verify the request was made correctly
            mock_client_instance.post.assert_called_once()
            call_args = mock_client_instance.post.call_args
            assert "data" in call_args.kwargs
            assert call_args.kwargs["data"]["username"] == "testuser"
            assert call_args.kwargs["data"]["password"] == "testpass"

    @pytest.mark.asyncio
    async def test_proxy_token_request_auth_failure(self):
        """Test token proxy request with authentication failure."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": "invalid_grant",
            "error_description": "Invalid user credentials",
        }
        mock_response.headers = {"content-type": "application/json"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            with pytest.raises(HTTPException) as exc_info:
                await auth_proxy.proxy_token_request(
                    username="wronguser",
                    password="wrongpass",
                    grant_type="password",
                    client_id="test-client",
                    client_secret="test-secret",
                )

            assert exc_info.value.status_code == 401
            assert "Authentication failed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_proxy_token_request_timeout(self):
        """Test token proxy request with timeout."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.post = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )

            with pytest.raises(HTTPException) as exc_info:
                await auth_proxy.proxy_token_request(
                    username="testuser",
                    password="testpass",
                )

            assert exc_info.value.status_code == 504
            assert "timeout" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_proxy_token_request_connection_error(self):
        """Test token proxy request with connection error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.post = AsyncMock(
                side_effect=httpx.RequestError("Connection failed")
            )

            with pytest.raises(HTTPException) as exc_info:
                await auth_proxy.proxy_token_request(
                    username="testuser",
                    password="testpass",
                )

            assert exc_info.value.status_code == 503
            assert "unavailable" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_proxy_token_request_generic_error(self):
        """Test token proxy request with generic error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.post = AsyncMock(side_effect=Exception("Unknown error"))

            with pytest.raises(HTTPException) as exc_info:
                await auth_proxy.proxy_token_request(
                    username="testuser",
                    password="testpass",
                )

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_proxy_token_request_non_json_error_response(self):
        """Test token proxy request with non-JSON error response."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.json.side_effect = ValueError("Not JSON")

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            with pytest.raises(HTTPException) as exc_info:
                await auth_proxy.proxy_token_request(
                    username="testuser",
                    password="testpass",
                )

            assert exc_info.value.status_code == 500


class TestGetRealmInfo:
    """Test get_realm_info endpoint."""

    @pytest.mark.asyncio
    async def test_get_realm_info_success(self):
        """Test successful realm info retrieval."""
        mock_realm_data = {
            "realm": "test-realm",
            "public_key": "test-public-key",
            "token-service": "https://keycloak.example.com/realms/test-realm",
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_realm_data

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get = AsyncMock(return_value=mock_response)

            result = await auth_proxy.get_realm_info()

            assert result == mock_realm_data
            mock_client_instance.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_realm_info_failure(self):
        """Test realm info retrieval failure."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get = AsyncMock(return_value=mock_response)

            with pytest.raises(HTTPException) as exc_info:
                await auth_proxy.get_realm_info()

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_realm_info_timeout(self):
        """Test realm info retrieval with timeout."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )

            with pytest.raises(HTTPException) as exc_info:
                await auth_proxy.get_realm_info()

            assert exc_info.value.status_code == 504

    @pytest.mark.asyncio
    async def test_get_realm_info_connection_error(self):
        """Test realm info retrieval with connection error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get = AsyncMock(
                side_effect=httpx.RequestError("Connection failed")
            )

            with pytest.raises(HTTPException) as exc_info:
                await auth_proxy.get_realm_info()

            assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_get_realm_info_generic_error(self):
        """Test realm info retrieval with generic error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get = AsyncMock(side_effect=Exception("Unknown error"))

            with pytest.raises(HTTPException) as exc_info:
                await auth_proxy.get_realm_info()

            assert exc_info.value.status_code == 500


class TestAuthProxyIntegration:
    """Integration tests for auth proxy endpoints."""

    def test_token_endpoint_with_test_client(self):
        """Test token endpoint with FastAPI test client."""
        client = TestClient(app)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "test-token",
                "expires_in": 3600,
                "refresh_expires_in": 7200,
                "refresh_token": "refresh-token",
                "token_type": "Bearer",
                "scope": "openid",
            }
            mock_response.headers = {"content-type": "application/json"}

            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            response = client.post(
                "/api/v1/auth-proxy/token",
                data={
                    "username": "testuser",
                    "password": "testpass",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["access_token"] == "test-token"

    def test_realm_info_endpoint_with_test_client(self):
        """Test realm info endpoint with FastAPI test client."""
        client = TestClient(app)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "realm": "test-realm",
                "public_key": "test-key",
            }

            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get = AsyncMock(return_value=mock_response)

            response = client.get("/api/v1/auth-proxy/realm-info")

            assert response.status_code == 200
            data = response.json()
            assert "realm" in data
            assert data["realm"] == "test-realm"

    def test_token_endpoint_schema_validation(self):
        """Test token endpoint validates required form fields."""
        client = TestClient(app)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "test-token",
                "expires_in": 3600,
                "refresh_expires_in": 7200,
                "refresh_token": "refresh-token",
                "token_type": "Bearer",
                "scope": "openid",
            }
            mock_response.headers = {"content-type": "application/json"}

            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            # Test missing username
            response = client.post(
                "/api/v1/auth-proxy/token",
                data={"password": "testpass"},
            )
            assert response.status_code == 422  # Validation error

            # Test missing password
            response = client.post(
                "/api/v1/auth-proxy/token",
                data={"username": "testuser"},
            )
            assert response.status_code == 422  # Validation error

