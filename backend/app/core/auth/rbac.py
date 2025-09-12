"""Role-Based Access Control (RBAC) for eShop application."""

from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.core.auth.keycloak import KeycloakUser, get_current_user_optional
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


class RBACConfig(BaseModel):
    """RBAC configuration for endpoints."""

    # Roles that can access command endpoints (write operations)
    command_roles: list[str] = ["admin", "manager"]

    # Roles that can access query endpoints (read operations)
    query_roles: list[str] = ["admin", "manager", "user"]

    # Default role for unauthenticated users (if any)
    default_role: str | None = None


# Default RBAC configuration
default_rbac_config = RBACConfig()


def require_command_access(
    rbac_config: RBACConfig = default_rbac_config,
) -> Callable[[KeycloakUser], Any]:
    """
    Dependency to require command access (admin/manager roles).

    Commands are write operations that modify data.
    """

    async def command_access_checker(
        current_user: KeycloakUser | None = Depends(get_current_user_optional),
        request: Request = None,
    ) -> KeycloakUser:
        """Check if user has command access."""
        if not current_user:
            # Log authentication failure for command access
            logger.log_security_event(
                event_type="authentication_failure",
                authentication_method="bearer_token",
                authorization_outcome="failure",
                source_ip=request.client.host if request and request.client else None,
                user_agent=request.headers.get("user-agent") if request else None,
                error="No authentication credentials provided",
                error_type="MissingCredentials",
                operation="command_access",
                required_roles=rbac_config.command_roles,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for command access",
            )

        # Check if user has any of the required command roles
        has_command_role = any(
            role in current_user.roles for role in rbac_config.command_roles
        )

        if not has_command_role:
            # Log authorization failure for command access
            logger.log_security_event(
                event_type="authorization_failure",
                user_id=current_user.sub,
                authentication_method="bearer_token",
                authorization_outcome="failure",
                source_ip=request.client.host if request and request.client else None,
                user_agent=request.headers.get("user-agent") if request else None,
                error=f"User lacks required command roles. User roles: {current_user.roles}, Required: {rbac_config.command_roles}",
                error_type="InsufficientPrivileges",
                operation="command_access",
                user_roles=current_user.roles,
                required_roles=rbac_config.command_roles,
            )
            logger.log_warning_with_context(
                "User attempted command access without required roles",
                context={
                    "username": current_user.preferred_username,
                    "user_roles": current_user.roles,
                    "required_roles": rbac_config.command_roles,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Command access requires one of: {', '.join(rbac_config.command_roles)}",
            )

        # Log successful command access
        logger.log_security_event(
            event_type="authorization_success",
            user_id=current_user.sub,
            authentication_method="bearer_token",
            authorization_outcome="success",
            source_ip=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            operation="command_access",
            user_roles=current_user.roles,
            required_roles=rbac_config.command_roles,
        )
        logger.info(
            f"User {current_user.preferred_username} granted command access "
            f"with roles: {current_user.roles}"
        )
        return current_user

    return command_access_checker


def require_query_access(
    rbac_config: RBACConfig = default_rbac_config,
) -> Callable[[KeycloakUser], Any]:
    """
    Dependency to require query access (admin/manager/user roles).

    Queries are read operations that don't modify data.
    """

    async def query_access_checker(
        current_user: KeycloakUser | None = Depends(get_current_user_optional),
        request: Request = None,
    ) -> KeycloakUser:
        """Check if user has query access."""
        if not current_user:
            # Log authentication failure for query access
            logger.log_security_event(
                event_type="authentication_failure",
                authentication_method="bearer_token",
                authorization_outcome="failure",
                source_ip=request.client.host if request and request.client else None,
                user_agent=request.headers.get("user-agent") if request else None,
                error="No authentication credentials provided",
                error_type="MissingCredentials",
                operation="query_access",
                required_roles=rbac_config.query_roles,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for query access",
            )

        # Check if user has any of the required query roles
        has_query_role = any(
            role in current_user.roles for role in rbac_config.query_roles
        )

        if not has_query_role:
            # Log authorization failure for query access
            logger.log_security_event(
                event_type="authorization_failure",
                user_id=current_user.sub,
                authentication_method="bearer_token",
                authorization_outcome="failure",
                source_ip=request.client.host if request and request.client else None,
                user_agent=request.headers.get("user-agent") if request else None,
                error=f"User lacks required query roles. User roles: {current_user.roles}, Required: {rbac_config.query_roles}",
                error_type="InsufficientPrivileges",
                operation="query_access",
                user_roles=current_user.roles,
                required_roles=rbac_config.query_roles,
            )
            logger.log_warning_with_context(
                "User attempted query access without required roles",
                context={
                    "username": current_user.preferred_username,
                    "user_roles": current_user.roles,
                    "required_roles": rbac_config.query_roles,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Query access requires one of: {', '.join(rbac_config.query_roles)}",
            )

        # Log successful query access
        logger.log_security_event(
            event_type="authorization_success",
            user_id=current_user.sub,
            authentication_method="bearer_token",
            authorization_outcome="success",
            source_ip=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            operation="query_access",
            user_roles=current_user.roles,
            required_roles=rbac_config.query_roles,
        )
        logger.log_debug_with_context(
            "User granted query access",
            context={
                "username": current_user.preferred_username,
                "user_roles": current_user.roles,
            },
        )
        return current_user

    return query_access_checker


def require_specific_role(required_role: str) -> Callable[[KeycloakUser], Any]:
    """
    Dependency to require a specific role.

    Args:
        required_role: The specific role required for access
    """

    async def specific_role_checker(
        current_user: KeycloakUser | None = Depends(get_current_user_optional),
    ) -> KeycloakUser:
        """Check if user has the specific required role."""
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        if required_role not in current_user.roles:
            logger.log_warning_with_context(
                "User attempted access without required role",
                context={
                    "username": current_user.preferred_username,
                    "required_role": required_role,
                    "user_roles": current_user.roles,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required",
            )

        logger.log_with_context(
            "User granted access with required role",
            context={
                "username": current_user.preferred_username,
                "required_role": required_role,
            },
        )
        return current_user

    return specific_role_checker


def require_any_role(required_roles: list[str]) -> Callable[[KeycloakUser], Any]:
    """
    Dependency to require any of the specified roles.

    Args:
        required_roles: List of roles, any of which grants access
    """

    async def any_role_checker(
        current_user: KeycloakUser | None = Depends(get_current_user_optional),
    ) -> KeycloakUser:
        """Check if user has any of the required roles."""
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        has_required_role = any(role in current_user.roles for role in required_roles)

        if not has_required_role:
            logger.log_warning_with_context(
                "User attempted access without required roles",
                context={
                    "username": current_user.preferred_username,
                    "user_roles": current_user.roles,
                    "required_roles": required_roles,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access requires one of: {', '.join(required_roles)}",
            )

        logger.log_with_context(
            "User granted access with required roles",
            context={
                "username": current_user.preferred_username,
                "user_roles": current_user.roles,
            },
        )
        return current_user

    return any_role_checker


# Convenience functions for common RBAC patterns
def require_admin() -> Callable[[KeycloakUser], Any]:
    """Require admin role for access."""
    return require_specific_role("admin")


def require_manager_or_admin() -> Callable[[KeycloakUser], Any]:
    """Require manager or admin role for access."""
    return require_any_role(["manager", "admin"])


def require_user_or_higher() -> Callable[[KeycloakUser], Any]:
    """Require user role or higher for access."""
    return require_any_role(["user", "manager", "admin"])


# RBAC decorator for functions
def rbac_protect(
    access_checker: Callable[[KeycloakUser], KeycloakUser],  # noqa: ARG001
) -> Callable[[Callable], Callable]:
    """
    Decorator to protect functions with RBAC.

    Args:
        access_checker: The RBAC dependency function to use
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # This is a simplified version - in practice, you'd need to
            # inject the dependency properly in FastAPI context
            # For now, this serves as documentation of intent
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# RBAC context manager for manual checks
class RBACContext:
    """Context manager for manual RBAC checks."""

    def __init__(self, user: KeycloakUser, required_roles: list[str]) -> None:
        """Initialize RBAC context."""
        self.user = user
        self.required_roles = required_roles
        self.has_access = any(role in user.roles for role in required_roles)

    def __enter__(self) -> "RBACContext":
        """Enter RBAC context."""
        if not self.has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access requires one of: {', '.join(self.required_roles)}",
            )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit RBAC context."""
        pass


# Utility functions for RBAC checks
def check_command_access(
    user: KeycloakUser, rbac_config: RBACConfig = default_rbac_config
) -> bool:
    """Check if user has command access."""
    return any(role in user.roles for role in rbac_config.command_roles)


def check_query_access(
    user: KeycloakUser, rbac_config: RBACConfig = default_rbac_config
) -> bool:
    """Check if user has query access."""
    return any(role in user.roles for role in rbac_config.query_roles)


def get_user_permissions(
    user: KeycloakUser, rbac_config: RBACConfig = default_rbac_config
) -> dict[str, bool]:
    """Get user permissions based on their roles."""
    return {
        "can_execute_commands": check_command_access(user, rbac_config),
        "can_execute_queries": check_query_access(user, rbac_config),
        "is_admin": "admin" in user.roles,
        "is_manager": "manager" in user.roles,
        "is_user": "user" in user.roles,
    }
