"""Tests for RBAC dependencies."""

from unittest.mock import MagicMock

import pytest
from app.core.auth.keycloak import KeycloakUser
from app.core.auth.rbac import (
    RBACConfig,
    RBACContext,
    check_command_access,
    check_query_access,
    get_user_permissions,
    require_admin,
    require_any_role,
    require_command_access,
    require_query_access,
    require_specific_role,
)
from fastapi import HTTPException


def _user(roles: list[str]) -> KeycloakUser:
    return KeycloakUser(
        sub="user-123",
        preferred_username="testuser",
        email="test@example.com",
        roles=roles,
    )


def _request() -> MagicMock:
    req = MagicMock()
    req.client.host = "127.0.0.1"
    req.headers = {"user-agent": "pytest"}
    return req


@pytest.mark.asyncio
async def test_command_access_requires_authentication() -> None:
    checker = require_command_access()
    with pytest.raises(HTTPException) as exc:
        await checker(request=_request(), current_user=None)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_command_access_forbidden_for_user_role() -> None:
    checker = require_command_access()
    with pytest.raises(HTTPException) as exc:
        await checker(request=_request(), current_user=_user(["user"]))
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_command_access_granted_for_admin() -> None:
    checker = require_command_access()
    user = _user(["admin"])
    result = await checker(request=_request(), current_user=user)
    assert result is user


@pytest.mark.asyncio
async def test_query_access_granted_for_user_role() -> None:
    checker = require_query_access()
    user = _user(["user"])
    result = await checker(request=_request(), current_user=user)
    assert result is user


@pytest.mark.asyncio
async def test_query_access_forbidden_without_roles() -> None:
    checker = require_query_access(RBACConfig(query_roles=["admin"]))
    with pytest.raises(HTTPException) as exc:
        await checker(request=_request(), current_user=_user(["user"]))
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_specific_role() -> None:
    checker = require_specific_role("manager")
    user = await checker(current_user=_user(["manager"]))
    assert user.preferred_username == "testuser"


@pytest.mark.asyncio
async def test_require_any_role() -> None:
    checker = require_any_role(["admin", "manager"])
    user = await checker(current_user=_user(["manager"]))
    assert "manager" in user.roles


@pytest.mark.asyncio
async def test_require_admin() -> None:
    checker = require_admin()
    with pytest.raises(HTTPException):
        await checker(current_user=_user(["manager"]))
    user = await checker(current_user=_user(["admin"]))
    assert user.preferred_username == "testuser"


def test_check_access_helpers() -> None:
    admin = _user(["admin"])
    regular = _user(["user"])
    assert check_command_access(admin) is True
    assert check_command_access(regular) is False
    assert check_query_access(regular) is True


def test_get_user_permissions() -> None:
    perms = get_user_permissions(_user(["admin", "manager"]))
    assert perms["can_execute_commands"] is True
    assert perms["is_admin"] is True


def test_rbac_context_allows_access() -> None:
    with RBACContext(_user(["manager"]), ["manager", "admin"]) as ctx:
        assert ctx.has_access is True


def test_rbac_context_denies_access() -> None:
    with pytest.raises(HTTPException):
        with RBACContext(_user(["user"]), ["admin"]):
            pass
