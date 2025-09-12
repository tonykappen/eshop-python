"""Keycloak authentication integration using fastapi-keycloak."""

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_keycloak import FastAPIKeycloak
from pydantic import BaseModel

from app.config.settings import settings
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)

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
            # First check if configuration is available
            if not self._check_config_available():
                logger.log_warning_with_context(
                    "Keycloak configuration not available - authentication will be disabled"
                )
                self.keycloak = None
                self._initialized = True
                return

            # Additional safety check - ensure all values are valid strings
            if (
                not isinstance(settings.keycloak_server_url, str)
                or not isinstance(settings.keycloak_client_id, str)
                or not isinstance(settings.keycloak_client_secret, str)
                or not isinstance(settings.keycloak_realm, str)
                or not isinstance(settings.keycloak_callback_uri, str)
            ):
                logger.warning(
                    "Keycloak configuration contains invalid types - authentication will be disabled"
                )
                self.keycloak = None
                self._initialized = True
                return

            try:
                # Initialize without admin client secret for basic authentication
                self.keycloak = FastAPIKeycloak(
                    server_url=settings.keycloak_server_url,
                    client_id=settings.keycloak_client_id,
                    client_secret=settings.keycloak_client_secret,
                    realm=settings.keycloak_realm,
                    callback_uri=settings.keycloak_callback_uri,
                    # Use empty string for admin client secret if not available
                    admin_client_secret="",
                )
                self._initialized = True
                logger.log_with_context(
                    "FastAPI Keycloak initialized successfully", "info"
                )
            except Exception as e:
                logger.log_exception("Failed to initialize Keycloak", exception=e)
                # Create a minimal instance for basic functionality
                self.keycloak = None
                self._initialized = True

    def is_available(self) -> bool:
        """Check if Keycloak service is available."""
        # Only initialize if we haven't tried yet
        if not self._initialized:
            self._initialize_keycloak()
        return self.keycloak is not None

    def force_initialize(self) -> None:
        """Force initialization of the Keycloak service."""
        if not self._initialized:
            self._initialize_keycloak()

    def _check_config_available(self) -> bool:
        """Check if all required Keycloak configuration settings are present."""
        logger.log_debug_with_context(
            "Checking Keycloak configuration",
            context={
                "server_url": settings.keycloak_server_url,
                "client_id": settings.keycloak_client_id,
                "client_secret": "***" if settings.keycloak_client_secret else "None",
                "realm": settings.keycloak_realm,
            },
        )

        result = (
            settings.keycloak_server_url is not None
            and settings.keycloak_server_url != ""
            and settings.keycloak_client_id is not None
            and settings.keycloak_client_id != ""
            and settings.keycloak_client_secret is not None
            and settings.keycloak_client_secret != ""
            and settings.keycloak_realm is not None
            and settings.keycloak_realm != ""
        )

        logger.log_debug_with_context(
            "Keycloak configuration check completed", context={"result": result}
        )
        return result

    async def verify_token(self, token: str) -> dict[str, Any]:
        """Verify JWT token with Keycloak."""
        # If Keycloak is not available, provide mock authentication for development
        if not self.is_available():
            logger.log_warning_with_context(
                "Keycloak not available - using mock authentication"
            )
            return await self._verify_token_mock(token)

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
                algorithms=settings.keycloak_jwt_algorithms,
                audience=[
                    "account",
                    settings.keycloak_client_id,
                ],  # Accept both "account" and client ID
                issuer=f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}",
            )
            return token_info  # type: ignore[no-any-return]
        except Exception as e:
            logger.log_exception("Token verification failed", exception=e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

    async def _verify_token_mock(self, token: str) -> dict[str, Any]:
        """Mock token verification for development when Keycloak is not available."""
        # For development, accept any non-empty token
        if not token or token.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Empty token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Return mock user data
        return {
            "sub": "mock-user-id",
            "email": "mock@example.com",
            "name": "Mock User",
            "preferred_username": "mockuser",
            "realm_access": {"roles": ["user", "admin"]},
        }

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
            logger.log_exception("Keycloak health check failed", exception=e)
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


# Global instance - will be initialized lazily
_keycloak_service_instance: KeycloakService | None = None


def get_keycloak_service() -> KeycloakService:
    """Get the Keycloak service instance, creating it if needed."""
    global _keycloak_service_instance
    if _keycloak_service_instance is None:
        _keycloak_service_instance = KeycloakService()
    return _keycloak_service_instance


# For backward compatibility
keycloak_service = get_keycloak_service()


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
        logger.log_warning_with_context(
            "Authentication failed", context={"error": str(e)}
        )
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
