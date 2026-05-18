"""Authentication proxy endpoints for frontend."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from app.config.settings import settings
from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/auth-proxy", tags=["auth-proxy"])

# Simple circuit breaker: after repeated transport failures, short-circuit for a cooldown.
_CONSECUTIVE_TRANSPORT_FAILURES = 0
_CIRCUIT_OPEN_UNTIL_MONO: float = 0.0
_CIRCUIT_FAILURE_THRESHOLD = 5
_CIRCUIT_OPEN_SECONDS = 30.0

# Three attempts; 1s and 2s sleep before the second and third try respectively.
_RETRY_BACKOFF_SECONDS = (1.0, 2.0)
_MAX_ATTEMPTS = 3


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    expires_in: int
    refresh_expires_in: int
    refresh_token: str
    token_type: str
    scope: str


def _check_circuit() -> None:
    global _CONSECUTIVE_TRANSPORT_FAILURES, _CIRCUIT_OPEN_UNTIL_MONO
    now = time.monotonic()
    if now < _CIRCUIT_OPEN_UNTIL_MONO:
        raise HTTPException(
            status_code=503,
            detail="Authentication service temporarily unavailable",
        )
    if _CIRCUIT_OPEN_UNTIL_MONO and now >= _CIRCUIT_OPEN_UNTIL_MONO:
        _CONSECUTIVE_TRANSPORT_FAILURES = 0
        _CIRCUIT_OPEN_UNTIL_MONO = 0.0


def _record_transport_success() -> None:
    global _CONSECUTIVE_TRANSPORT_FAILURES
    _CONSECUTIVE_TRANSPORT_FAILURES = 0


def _record_transport_failure_after_retries() -> None:
    global _CONSECUTIVE_TRANSPORT_FAILURES, _CIRCUIT_OPEN_UNTIL_MONO
    _CONSECUTIVE_TRANSPORT_FAILURES += 1
    if _CONSECUTIVE_TRANSPORT_FAILURES > _CIRCUIT_FAILURE_THRESHOLD:
        _CIRCUIT_OPEN_UNTIL_MONO = time.monotonic() + _CIRCUIT_OPEN_SECONDS


def _raise_for_last_transport_error(exc: Exception) -> None:
    if isinstance(exc, httpx.ConnectError):
        raise HTTPException(
            status_code=502,
            detail="Authentication service connection failed",
        ) from None
    if isinstance(exc, httpx.TimeoutException):
        raise HTTPException(
            status_code=504,
            detail="Authentication service timeout",
        ) from None
    if isinstance(exc, httpx.RequestError):
        raise HTTPException(
            status_code=503,
            detail=f"Authentication service unavailable: {exc!s}",
        ) from exc
    raise HTTPException(status_code=500, detail=f"Internal error: {exc!s}") from exc


async def _request_with_retries(
    execute: Callable[[httpx.AsyncClient], Awaitable[httpx.Response]],
) -> httpx.Response:
    """Run ``execute(client)`` up to three times; backoff 1s and 2s between tries."""
    last_error: Exception | None = None
    async with httpx.AsyncClient() as client:
        for attempt in range(_MAX_ATTEMPTS):
            try:
                response = await execute(client)
                _record_transport_success()
                return response
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_error = e
                if attempt < _MAX_ATTEMPTS - 1:
                    await asyncio.sleep(_RETRY_BACKOFF_SECONDS[attempt])
            except httpx.RequestError as e:
                last_error = e
                if attempt < _MAX_ATTEMPTS - 1:
                    await asyncio.sleep(_RETRY_BACKOFF_SECONDS[attempt])
                else:
                    break

    if last_error is None:
        raise RuntimeError("auth proxy retry loop exited without response or error")
    _record_transport_failure_after_retries()
    _raise_for_last_transport_error(last_error)


@router.post("/token", response_model=TokenResponse)
async def proxy_token_request(
    username: str = Form(...),
    password: str = Form(...),
    grant_type: str = Form(default=settings.keycloak_grant_type),
) -> TokenResponse:
    """
    Proxy token requests to Keycloak.

    This endpoint acts as a proxy between the frontend and Keycloak
    to work around browser security restrictions on localhost requests.

    SECURITY: Client credentials (client_id and client_secret) are handled
    server-side from settings to prevent exposure in browser network requests.
    The frontend should NOT send these values.
    """
    _check_circuit()

    client_id = settings.keycloak_client_id
    client_secret = settings.keycloak_client_secret
    url = (
        f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}"
        "/protocol/openid-connect/token"
    )
    data = {
        "username": username,
        "password": password,
        "grant_type": grant_type,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:

        async def do_post(client: httpx.AsyncClient) -> httpx.Response:
            return await client.post(
                url,
                data=data,
                headers=headers,
                timeout=10.0,
            )

        response = await _request_with_retries(do_post)

        if response.status_code == 200:
            token_data = response.json()
            return TokenResponse(**token_data)
        error_data = (
            response.json()
            if response.headers.get("content-type") == "application/json"
            else {"error": "authentication_failed"}
        )
        raise HTTPException(
            status_code=response.status_code,
            detail=(
                "Authentication failed: "
                f"{error_data.get('error_description', error_data.get('error', 'Unknown error'))}"
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal authentication error: {e!s}"
        ) from e


@router.get("/realm-info")
async def get_realm_info() -> dict[str, Any]:
    """Get Keycloak realm information."""
    _check_circuit()

    url = f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}"

    try:

        async def do_get(client: httpx.AsyncClient) -> httpx.Response:
            return await client.get(url, timeout=10.0)

        response = await _request_with_retries(do_get)

        if response.status_code == 200:
            return response.json()
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch realm information",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e!s}") from e
