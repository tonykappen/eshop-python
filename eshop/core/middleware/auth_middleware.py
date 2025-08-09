"""Authentication middleware for Keycloak integration."""

import logging
from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from eshop.core.auth.keycloak import KeycloakUser, keycloak_service

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    request: Request,  # noqa: ARG001
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> KeycloakUser | None:
    """Get current user if authenticated, otherwise return None."""
    if not credentials:
        return None

    try:
        return await keycloak_service.get_user_info(credentials.credentials)
    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        return None


async def get_current_user_optional_from_request(
    request: Request,
) -> KeycloakUser | None:
    """Get current user from request (for middleware)."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.replace("Bearer ", "")
    try:
        return await keycloak_service.get_user_info(token)
    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        return None


async def get_current_user_required(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> KeycloakUser:
    """Get current authenticated user, raise 401 if not authenticated."""
    try:
        return await keycloak_service.get_user_info(credentials.credentials)
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def require_role(required_role: str) -> Callable[[KeycloakUser], Any]:
    """Dependency to require specific role."""

    async def role_checker(
        current_user: KeycloakUser = Depends(get_current_user_required),
    ) -> KeycloakUser:
        has_role = await keycloak_service.check_role(current_user, required_role)
        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required",
            )
        return current_user

    return role_checker


def add_auth_middleware(app: Any) -> Any:
    """Add authentication middleware to FastAPI app."""

    # Add user to request state for optional authentication
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next: Any) -> Any:
        # Add user to request state if authenticated
        user = await get_current_user_optional_from_request(request)
        request.state.user = user

        response = await call_next(request)
        return response

    return None  # Actually return None as this modifies app in-place
