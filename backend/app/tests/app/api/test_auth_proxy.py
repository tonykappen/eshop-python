"""Tests for auth proxy endpoints."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from app.api import auth_proxy
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_circuit() -> None:
    auth_proxy._CONSECUTIVE_TRANSPORT_FAILURES = 0
    auth_proxy._CIRCUIT_OPEN_UNTIL_MONO = 0.0
    yield
    auth_proxy._CONSECUTIVE_TRANSPORT_FAILURES = 0
    auth_proxy._CIRCUIT_OPEN_UNTIL_MONO = 0.0


def test_check_circuit_open_raises_503() -> None:
    auth_proxy._CIRCUIT_OPEN_UNTIL_MONO = auth_proxy.time.monotonic() + 60
    with pytest.raises(auth_proxy.HTTPException) as exc:
        auth_proxy._check_circuit()
    assert exc.value.status_code == 503


def test_raise_for_connect_error() -> None:
    with pytest.raises(auth_proxy.HTTPException) as exc:
        auth_proxy._raise_for_last_transport_error(httpx.ConnectError("fail"))
    assert exc.value.status_code == 502


def test_raise_for_timeout() -> None:
    with pytest.raises(auth_proxy.HTTPException) as exc:
        auth_proxy._raise_for_last_transport_error(httpx.TimeoutException("slow"))
    assert exc.value.status_code == 504


def test_token_login_success(client: TestClient) -> None:
    mock_response = httpx.Response(
        200,
        json={
            "access_token": "token",
            "expires_in": 300,
            "refresh_expires_in": 1800,
            "refresh_token": "refresh",
            "token_type": "Bearer",
            "scope": "openid",
        },
        request=httpx.Request("POST", "http://keycloak/token"),
    )

    with patch(
        "app.api.auth_proxy._request_with_retries",
        new=AsyncMock(return_value=mock_response),
    ):
        response = client.post(
            "/api/v1/auth-proxy/token",
            data={"username": "user", "password": "pass"},
        )

    assert response.status_code == 200
    assert response.json()["access_token"] == "token"
