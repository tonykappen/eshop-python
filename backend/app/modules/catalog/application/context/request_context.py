"""Request context for holding tenant/user info for auditing/policies."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class RequestContext(BaseModel):
    """Request context holding tenant/user info for auditing/policies."""

    # User information
    user_id: UUID | None = Field(None, description="Current user ID")
    username: str | None = Field(None, description="Current username")
    user_roles: list[str] = Field(default_factory=list, description="User roles")

    # Tenant information
    tenant_id: UUID | None = Field(None, description="Current tenant ID")
    tenant_name: str | None = Field(None, description="Current tenant name")

    # Request information
    request_id: str | None = Field(None, description="Request ID for tracing")
    correlation_id: str | None = Field(
        None, description="Correlation ID for tracing"
    )

    # Additional context
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.user_id is not None

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return "admin" in self.user_roles

    @property
    def is_manager(self) -> bool:
        """Check if user has manager role."""
        return "manager" in self.user_roles

    @property
    def is_user(self) -> bool:
        """Check if user has user role."""
        return "user" in self.user_roles

    def has_role(self, role: str) -> bool:
        """
        Check if user has a specific role.

        Args:
            role: Role to check

        Returns:
            True if user has the role, False otherwise
        """
        return role in self.user_roles

    def has_any_role(self, roles: list[str]) -> bool:
        """
        Check if user has any of the specified roles.

        Args:
            roles: List of roles to check

        Returns:
            True if user has any of the roles, False otherwise
        """
        return any(role in self.user_roles for role in roles)

    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to the context.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata from the context.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)

    def to_dict(self) -> dict:
        """Convert context to dictionary."""
        return {
            "user_id": str(self.user_id) if self.user_id else None,
            "username": self.username,
            "user_roles": self.user_roles,
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "tenant_name": self.tenant_name,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
            "is_authenticated": self.is_authenticated,
            "is_admin": self.is_admin,
            "is_manager": self.is_manager,
            "is_user": self.is_user,
        }
