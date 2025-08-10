"""Authentication proxy endpoints for frontend."""

from typing import Any

import httpx
from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel

from app.config.settings import settings

router = APIRouter(prefix="/auth-proxy", tags=["auth-proxy"])


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    expires_in: int
    refresh_expires_in: int
    refresh_token: str
    token_type: str
    scope: str


@router.post("/token", response_model=TokenResponse)
async def proxy_token_request(
    username: str = Form(...),
    password: str = Form(...),
    grant_type: str = Form(default="password"),
    client_id: str = Form(default="eshop-api"),
    client_secret: str = Form(default="your-client-secret"),
) -> TokenResponse:
    """
    Proxy token requests to Keycloak.

    This endpoint acts as a proxy between the frontend and Keycloak
    to work around browser security restrictions on localhost requests.
    """
    try:
        # Make request to Keycloak from backend
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token",
                data={
                    "username": username,
                    "password": password,
                    "grant_type": grant_type,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0,
            )

            if response.status_code == 200:
                token_data = response.json()
                return TokenResponse(**token_data)
            else:
                # Return Keycloak error details
                error_data = (
                    response.json()
                    if response.headers.get("content-type") == "application/json"
                    else {"error": "authentication_failed"}
                )
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Authentication failed: {error_data.get('error_description', error_data.get('error', 'Unknown error'))}",
                )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504, detail="Authentication service timeout"
        ) from None
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503, detail=f"Authentication service unavailable: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal authentication error: {str(e)}"
        ) from e


@router.get("/realm-info")
async def get_realm_info() -> dict[str, Any]:
    """Get Keycloak realm information."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}",
                timeout=10.0,
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch realm information",
                )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504, detail="Authentication service timeout"
        ) from None
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503, detail=f"Authentication service unavailable: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}") from e
