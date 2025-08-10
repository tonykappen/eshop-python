"""Keycloak authentication integration using fastapi-keycloak."""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_keycloak import FastAPIKeycloak
from pydantic import BaseModel

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


class KeycloakUser(BaseModel):
    """Keycloak user model."""

    sub: str
    email: str | None = None
    name: str | None = None
    preferred_username: str | None = None
    roles: list[str] = []


class KeycloakService:
    """Keycloak authentication service using fastapi-keycloak."""

    def __init__(self) -> None:
        """Initialize Keycloak service."""
        self.keycloak = None
        self._initialized = False

    def _initialize_keycloak(self) -> None:
        """Initialize Keycloak connection lazily."""
        if not self._initialized:
            try:
                # Initialize without admin client secret for basic authentication
                self.keycloak = FastAPIKeycloak(
                    server_url=settings.keycloak_server_url,
                    client_id=settings.keycloak_client_id,
                    client_secret=settings.keycloak_client_secret,
                    realm=settings.keycloak_realm,
                    callback_uri=settings.keycloak_callback_uri,
                    # Don't require admin access for basic functionality
                    admin_client_secret=None,
                )
                self._initialized = True
                logger.info("FastAPI Keycloak initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Keycloak: {e}")
                # Create a minimal instance for basic functionality
                self.keycloak = None

    async def verify_token(self, token: str) -> dict[str, Any]:
        """Verify JWT token with Keycloak."""
        try:
            # For now, use a simple JWT decode approach
            import jwt
            from jwt import PyJWKClient

            # Get the public key from Keycloak
            jwks_url = f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/certs"
            jwks_client = PyJWKClient(jwks_url)

            # Decode the token
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            token_info = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=[
                    "account",
                    settings.keycloak_client_id,
                ],  # Accept both "account" and client ID
                issuer=f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}",
            )
            return token_info  # type: ignore[no-any-return]
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

    async def get_user_info(self, token: str) -> KeycloakUser:
        """Get user information from token."""
        token_info = await self.verify_token(token)

        # Extract user information
        user = KeycloakUser(
            sub=token_info.get("sub", ""),
            email=token_info.get("email"),
            name=token_info.get("name"),
            preferred_username=token_info.get("preferred_username"),
            roles=token_info.get("realm_access", {}).get("roles", []),
        )

        return user

    async def check_role(self, user: KeycloakUser, required_role: str) -> bool:
        """Check if user has required role."""
        return required_role in user.roles

    async def health_check(self) -> dict[str, Any]:
        """Check Keycloak service health."""
        try:
            # Simple HTTP check to Keycloak server
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}"
                )
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "service": "keycloak",
                        "realm": settings.keycloak_realm,
                        "server_url": settings.keycloak_server_url,
                        "response_time": "OK",
                    }
                else:
                    raise Exception(f"HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"Keycloak health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "keycloak",
                "error": str(e),
            }

    def get_current_user_dependency(self) -> Any:
        """Get FastAPI dependency for current user."""
        self._initialize_keycloak()
        if self.keycloak is None:
            raise Exception("Keycloak not initialized")
        return self.keycloak.get_current_user()

    def require_role_dependency(self, required_role: str) -> Any:
        """Get FastAPI dependency to require specific role."""
        self._initialize_keycloak()
        if self.keycloak is None:
            raise Exception("Keycloak not initialized")
        return self.keycloak.require_roles(required_role)


# Global instance
keycloak_service = KeycloakService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> KeycloakUser:
    """Get current authenticated user."""
    if not credentials:
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
        return await keycloak_service.get_user_info(credentials.credentials)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> KeycloakUser | None:
    """Get current user if authenticated, otherwise return None."""
    if not credentials:
        return None
    if not credentials.credentials:
        return None

    try:
        return await keycloak_service.get_user_info(credentials.credentials)
    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        return None


def require_role(
    required_role: str,
) -> Callable[[KeycloakUser], Awaitable[KeycloakUser]]:
    """Dependency to require specific role."""

    async def role_checker(
        current_user: KeycloakUser = Depends(
            get_current_user
        ),  # Use the required version
    ) -> KeycloakUser:
        has_role = await keycloak_service.check_role(current_user, required_role)
        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required",
            )
        return current_user

    return role_checker


# FastAPI Keycloak integration helpers
def get_keycloak_app() -> Any:
    """Get the FastAPI Keycloak app instance."""
    keycloak_service._initialize_keycloak()
    return keycloak_service.keycloak


def add_keycloak_routes(app: Any) -> Any:
    """Add Keycloak routes to FastAPI app."""
    keycloak_service._initialize_keycloak()
    if keycloak_service.keycloak is not None:
        keycloak_service.keycloak.add_auth_routes(app)
    return app
