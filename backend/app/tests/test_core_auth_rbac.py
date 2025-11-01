"""Comprehensive tests for RBAC module with schema validation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request, status
from fastapi.testclient import TestClient

from app.core.auth.keycloak import KeycloakUser
from app.core.auth.rbac import (
    RBACConfig,
    check_command_access,
    check_query_access,
    get_user_permissions,
    require_admin,
    require_any_role,
    require_command_access,
    require_manager_or_admin,
    require_query_access,
    require_specific_role,
    require_user_or_higher,
)


class TestRBACConfig:
    """Test RBAC configuration schema."""

    def test_rbac_config_default_values(self):
        """Test RBACConfig with default values."""
        config = RBACConfig()
        assert config.command_roles == ["admin", "manager"]
        assert config.query_roles == ["admin", "manager", "user"]
        assert config.default_role is None

    def test_rbac_config_custom_values(self):
        """Test RBACConfig with custom values."""
        config = RBACConfig(
            command_roles=["superadmin"],
            query_roles=["viewer", "user"],
            default_role="guest",
        )
        assert config.command_roles == ["superadmin"]
        assert config.query_roles == ["viewer", "user"]
        assert config.default_role == "guest"

    def test_rbac_config_validation(self):
        """Test RBACConfig schema validation."""
        # Test with empty roles
        config = RBACConfig(command_roles=[], query_roles=[])
        assert config.command_roles == []
        assert config.query_roles == []


class TestRequireCommandAccess:
    """Test require_command_access dependency."""

    @pytest.mark.asyncio
    async def test_require_command_access_with_admin_role(self):
        """Test command access with admin role."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = ["admin"]
        mock_user.sub = "user-123"
        mock_user.preferred_username = "admin_user"

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        checker = require_command_access()
        result = await checker(current_user=mock_user, request=mock_request)

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_require_command_access_with_manager_role(self):
        """Test command access with manager role."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = ["manager"]
        mock_user.sub = "user-123"
        mock_user.preferred_username = "manager_user"

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        checker = require_command_access()
        result = await checker(current_user=mock_user, request=mock_request)

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_require_command_access_without_user(self):
        """Test command access without authenticated user."""
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        checker = require_command_access()

        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=None, request=mock_request)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Authentication required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_require_command_access_with_insufficient_roles(self):
        """Test command access with insufficient roles."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = ["user"]  # Only user role, not admin or manager
        mock_user.sub = "user-123"
        mock_user.preferred_username = "regular_user"

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        checker = require_command_access()

        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user, request=mock_request)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Command access requires" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_require_command_access_custom_config(self):
        """Test command access with custom RBAC config."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = ["superadmin"]
        mock_user.sub = "user-123"
        mock_user.preferred_username = "superadmin_user"

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        custom_config = RBACConfig(command_roles=["superadmin"])
        checker = require_command_access(custom_config)
        result = await checker(current_user=mock_user, request=mock_request)

        assert result == mock_user


class TestRequireQueryAccess:
    """Test require_query_access dependency."""

    @pytest.mark.asyncio
    async def test_require_query_access_with_user_role(self):
        """Test query access with user role."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = ["user"]
        mock_user.sub = "user-123"
        mock_user.preferred_username = "regular_user"

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        checker = require_query_access()
        result = await checker(current_user=mock_user, request=mock_request)

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_require_query_access_without_user(self):
        """Test query access without authenticated user."""
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        checker = require_query_access()

        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=None, request=mock_request)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_require_query_access_with_insufficient_roles(self):
        """Test query access with insufficient roles."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = ["guest"]  # Not in query_roles
        mock_user.sub = "user-123"
        mock_user.preferred_username = "guest_user"

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        checker = require_query_access()

        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user, request=mock_request)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestRequireSpecificRole:
    """Test require_specific_role dependency."""

    @pytest.mark.asyncio
    async def test_require_specific_role_success(self):
        """Test require_specific_role with matching role."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = ["admin"]
        mock_user.sub = "user-123"
        mock_user.preferred_username = "admin_user"

        checker = require_specific_role("admin")
        result = await checker(current_user=mock_user)

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_require_specific_role_failure(self):
        """Test require_specific_role without matching role."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = ["user"]
        mock_user.sub = "user-123"
        mock_user.preferred_username = "regular_user"

        checker = require_specific_role("admin")

        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "admin" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_require_specific_role_no_user(self):
        """Test require_specific_role without user."""
        checker = require_specific_role("admin")

        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=None)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestRequireAnyRole:
    """Test require_any_role dependency."""

    @pytest.mark.asyncio
    async def test_require_any_role_success(self):
        """Test require_any_role with one matching role."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = ["manager"]
        mock_user.sub = "user-123"
        mock_user.preferred_username = "manager_user"

        checker = require_any_role(["admin", "manager"])
        result = await checker(current_user=mock_user)

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_require_any_role_failure(self):
        """Test require_any_role without matching roles."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = ["user"]
        mock_user.sub = "user-123"
        mock_user.preferred_username = "regular_user"

        checker = require_any_role(["admin", "manager"])

        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestConvenienceFunctions:
    """Test convenience RBAC functions."""

    @pytest.mark.asyncio
    async def test_require_admin(self):
        """Test require_admin convenience function."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = ["admin"]
        mock_user.preferred_username = "admin_user"

        checker = require_admin()
        result = await checker(current_user=mock_user)

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_require_manager_or_admin(self):
        """Test require_manager_or_admin convenience function."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = ["manager"]
        mock_user.preferred_username = "manager_user"

        checker = require_manager_or_admin()
        result = await checker(current_user=mock_user)

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_require_user_or_higher(self):
        """Test require_user_or_higher convenience function."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = ["user"]
        mock_user.preferred_username = "regular_user"

        checker = require_user_or_higher()
        result = await checker(current_user=mock_user)

        assert result == mock_user


class TestUtilityFunctions:
    """Test RBAC utility functions."""

    def test_check_command_access(self):
        """Test check_command_access utility."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = ["admin"]

        assert check_command_access(mock_user) is True

        mock_user.roles = ["user"]
        assert check_command_access(mock_user) is False

    def test_check_query_access(self):
        """Test check_query_access utility."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = ["user"]

        assert check_query_access(mock_user) is True

        mock_user.roles = ["guest"]
        assert check_query_access(mock_user) is False

    def test_get_user_permissions(self):
        """Test get_user_permissions utility."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = ["admin"]

        permissions = get_user_permissions(mock_user)

        assert permissions["can_execute_commands"] is True
        assert permissions["can_execute_queries"] is True
        assert permissions["is_admin"] is True
        assert permissions["is_manager"] is False
        assert permissions["is_user"] is False

        # Test with user role
        mock_user.roles = ["user"]
        permissions = get_user_permissions(mock_user)

        assert permissions["can_execute_commands"] is False
        assert permissions["can_execute_queries"] is True
        assert permissions["is_admin"] is False
        assert permissions["is_user"] is True


class TestRBACEdgeCases:
    """Test RBAC edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_command_access_with_empty_roles(self):
        """Test command access with user having empty roles."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = []
        mock_user.sub = "user-123"
        mock_user.preferred_username = "no_role_user"

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        checker = require_command_access()

        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user, request=mock_request)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_query_access_with_empty_roles(self):
        """Test query access with user having empty roles."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = []
        mock_user.sub = "user-123"
        mock_user.preferred_username = "no_role_user"

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-agent"}

        checker = require_query_access()

        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user, request=mock_request)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_command_access_with_request_no_client(self):
        """Test command access when request has no client."""
        mock_user = MagicMock(spec=KeycloakUser)
        mock_user.roles = ["admin"]
        mock_user.sub = "user-123"
        mock_user.preferred_username = "admin_user"

        mock_request = MagicMock(spec=Request)
        mock_request.client = None
        mock_request.headers = {}

        checker = require_command_access()
        result = await checker(current_user=mock_user, request=mock_request)

        # Should still work, just without client info
        assert result == mock_user

