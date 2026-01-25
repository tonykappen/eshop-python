"""Keycloak authentication integration using fastapi-keycloak."""

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
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
    jti: str | None = None  # JWT Token ID
    sid: str | None = None  # Keycloak Session ID


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
                # Initialize Keycloak client with proper configuration
                # We'll use a custom approach to avoid admin token issues
                from fastapi_keycloak.api import FastAPIKeycloak

                # Create the instance without calling __init__ to avoid admin token retrieval
                self.keycloak = object.__new__(FastAPIKeycloak)

                # Add missing attributes that FastAPIKeycloak expects FIRST
                self.keycloak.timeout = 30  # Default timeout
                self.keycloak.ssl_verification = True
                self.keycloak.auto_update_token = True
                self.keycloak._public_key = None
                self.keycloak._realm_uri = (
                    f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}"
                )

                # Set the required attributes manually
                self.keycloak.server_url = settings.keycloak_server_url
                self.keycloak.client_id = settings.keycloak_client_id
                self.keycloak.client_secret = settings.keycloak_client_secret
                self.keycloak.realm = settings.keycloak_realm
                self.keycloak.callback_uri = settings.keycloak_callback_uri

                # Initialize other required attributes
                self.keycloak._realm_url = (
                    f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}"
                )
                self.keycloak._well_known = None
                self.keycloak._jwks = None

                # Set admin token properties AFTER setting all other attributes
                # Don't set admin_token property as it triggers JWT decode
                self.keycloak._admin_token = None

                self._initialized = True
                logger.log_with_context(
                    "FastAPI Keycloak initialized successfully", "info"
                )
            except Exception as e:
                logger.log_exception("Failed to initialize Keycloak", exception=e)
                # Keycloak is required - do not fall back to mock authentication
                self.keycloak = None
                self._initialized = True
                logger.log_error_with_context(
                    "Keycloak initialization failed - authentication will not work"
                )

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

        # Checking for empty string is not a security issue - it's validation
        result = (
            settings.keycloak_server_url is not None
            and settings.keycloak_server_url != ""
            and settings.keycloak_client_id is not None
            and settings.keycloak_client_id != ""
            and settings.keycloak_client_secret is not None
            and settings.keycloak_client_secret != ""  # nosec B105
            and settings.keycloak_realm is not None
            and settings.keycloak_realm != ""
        )

        logger.log_debug_with_context(
            "Keycloak configuration check completed", context={"result": result}
        )
        return result

    async def verify_token(self, token: str) -> dict[str, Any]:
        """Verify JWT token with Keycloak."""
        # Ensure Keycloak is available before attempting token verification
        if not self.is_available():
            logger.log_error_with_context(
                "Keycloak not available - authentication cannot proceed"
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            # Use JWT decode approach with Keycloak
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
                leeway=7200,  # Allow 2 hours leeway for time synchronization issues
            )
            return token_info  # type: ignore[no-any-return]
        except Exception as e:
            logger.log_exception("Token verification failed", exception=e)
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
            jti=token_info.get("jti"),  # JWT Token ID
            sid=token_info.get("sid"),  # Keycloak Session ID
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
    """Add Keycloak routes and Swagger configuration to FastAPI app."""
    keycloak_service._initialize_keycloak()
    if keycloak_service.keycloak is not None:
        # FastAPIKeycloak provides add_swagger_config to add OAuth2 authentication to Swagger UI
        if hasattr(keycloak_service.keycloak, "add_swagger_config"):
            try:
                keycloak_service.keycloak.add_swagger_config(app)
                logger.log_with_context(
                    "[OK] Keycloak Swagger configuration added successfully", "info"
                )
            except Exception as e:
                logger.log_warning_with_context(
                    "Failed to add Keycloak Swagger config", context={"error": str(e)}
                )

        # Check for router attribute to include authentication routes
        if hasattr(keycloak_service.keycloak, "router"):
            try:
                router = getattr(keycloak_service.keycloak, "router", None)
                if router:
                    app.include_router(router)
                    logger.log_with_context(
                        "[OK] Keycloak authentication routes added successfully", "info"
                    )
            except Exception as e:
                logger.log_warning_with_context(
                    "Failed to include Keycloak router", context={"error": str(e)}
                )

        # Check for add_auth_routes method (older/different versions)
        elif hasattr(keycloak_service.keycloak, "add_auth_routes"):
            try:
                keycloak_service.keycloak.add_auth_routes(app)
                logger.log_with_context(
                    "[OK] Keycloak authentication routes added successfully", "info"
                )
            except Exception as e:
                logger.log_warning_with_context(
                    "Failed to add Keycloak auth routes", context={"error": str(e)}
                )
        else:
            # Authentication still works via middleware and dependencies
            # Swagger config might be the only thing we can add
            logger.log_debug_with_context(
                "Keycloak route methods not found - authentication works via middleware and dependencies"
            )
    return app
