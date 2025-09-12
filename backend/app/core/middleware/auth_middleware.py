"""Authentication middleware for Keycloak integration."""

from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth.keycloak import KeycloakUser, keycloak_service
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


# This function is now defined in keycloak.py to avoid circular imports


async def get_current_user_optional_from_request(
    request: Request,
) -> KeycloakUser | None:
    """Get current user from request (for middleware)."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.replace("Bearer ", "")
    if not token.strip():
        return None

    try:
        user = await keycloak_service.get_user_info(token)
        # Log successful authentication
        logger.log_security_event(
            event_type="authentication_success",
            user_id=user.sub if user else None,
            authentication_method="bearer_token",
            authorization_outcome="success",
            source_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return user
    except Exception as e:
        # Log failed authentication
        logger.log_security_event(
            event_type="authentication_failure",
            authentication_method="bearer_token",
            authorization_outcome="failure",
            source_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            error=str(e),
            error_type=type(e).__name__,
        )
        logger.log_warning_with_context(
            "Authentication failed", context={"error": str(e)}
        )
        return None


async def get_current_user_required(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> KeycloakUser:
    """Get current authenticated user, raise 401 if not authenticated."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await keycloak_service.get_user_info(credentials.credentials)
        # Log successful authentication
        logger.log_security_event(
            event_type="authentication_success",
            user_id=user.sub if user else None,
            authentication_method="bearer_token",
            authorization_outcome="success",
        )
        return user
    except Exception as e:
        # Log failed authentication
        logger.log_security_event(
            event_type="authentication_failure",
            authentication_method="bearer_token",
            authorization_outcome="failure",
            error=str(e),
            error_type=type(e).__name__,
        )
        logger.log_error_with_context(
            "Authentication failed", error=e, error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


# This function is now defined in keycloak.py to avoid duplication


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
