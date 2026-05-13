"""Keycloak credentials management module."""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


class MasterAdminCredentials(BaseModel):
    """Master admin credentials."""

    username: str = "admin"
    password: str = "admin"


class RealmAdminCredentials(BaseModel):
    """Realm admin credentials."""

    username: str
    email: str
    password: str
    first_name: str = Field(alias="first_name")
    last_name: str = Field(alias="last_name")

    class Config:
        """Pydantic config."""

        populate_by_name = True


class ClientConfig(BaseModel):
    """OAuth/OIDC client configuration."""

    client_id: str = Field(alias="client_id")
    client_secret: str = Field(alias="client_secret")
    redirect_uris: list[str] = Field(default_factory=list, alias="redirect_uris")
    web_origins: list[str] = Field(default_factory=list, alias="web_origins")
    service_accounts_enabled: bool = Field(
        default=True, alias="service_accounts_enabled"
    )
    authorization_services_enabled: bool = Field(
        default=True, alias="authorization_services_enabled"
    )
    direct_access_grants_enabled: bool = Field(
        default=True, alias="direct_access_grants_enabled"
    )
    standard_flow_enabled: bool = Field(default=True, alias="standard_flow_enabled")

    class Config:
        """Pydantic config."""

        populate_by_name = True


class RoleConfig(BaseModel):
    """Role configuration."""

    name: str
    description: str = ""


class UserConfig(BaseModel):
    """User configuration."""

    username: str
    email: str
    password: str
    first_name: str = Field(alias="first_name")
    last_name: str = Field(alias="last_name")
    roles: list[str] = Field(default_factory=list)
    email_verified: bool = Field(default=True, alias="email_verified")
    enabled: bool = True

    class Config:
        """Pydantic config."""

        populate_by_name = True


class RoleHierarchyConfig(BaseModel):
    """Role hierarchy configuration."""

    includes: list[str] = Field(default_factory=list)


class KeycloakCredentials(BaseModel):
    """Complete Keycloak credentials configuration."""

    master_admin: MasterAdminCredentials = Field(
        default_factory=MasterAdminCredentials, alias="master_admin"
    )
    realm_admin: RealmAdminCredentials
    clients: list[ClientConfig] = Field(default_factory=list)
    roles: list[RoleConfig] = Field(default_factory=list)
    users: list[UserConfig] = Field(default_factory=list)
    role_hierarchy: dict[str, RoleHierarchyConfig] = Field(
        default_factory=dict, alias="role_hierarchy"
    )

    class Config:
        """Pydantic config."""

        populate_by_name = True


class CredentialsLoader:
    """Load and validate Keycloak credentials from file."""

    def __init__(self, credentials_path: str | Path | None = None) -> None:
        """Initialize credentials loader.

        Args:
            credentials_path: Path to credentials file. If None, will search in standard locations.
        """
        self.credentials_path = self._resolve_credentials_path(credentials_path)
        self._credentials: KeycloakCredentials | None = None

    def _resolve_credentials_path(self, path: str | Path | None = None) -> Path:
        """Resolve the path to the credentials file.

        Search order:
        1. Provided path
        2. KEYCLOAK_CREDENTIALS_PATH environment variable
        3. ./keycloak_credentials.yaml
        4. ./infra/keycloak/credentials.yaml
        5. Fall back to example file

        Args:
            path: Optional path to credentials file

        Returns:
            Resolved path to credentials file
        """
        # Try provided path
        if path:
            resolved = Path(path)
            if resolved.exists():
                logger.info(f"Using credentials file: {resolved}")
                return resolved

        # Try environment variable
        env_path = os.getenv("KEYCLOAK_CREDENTIALS_PATH")
        if env_path:
            resolved = Path(env_path)
            if resolved.exists():
                logger.info(f"Using credentials file from env: {resolved}")
                return resolved
            else:
                logger.warning(
                    f"KEYCLOAK_CREDENTIALS_PATH points to non-existent file: {env_path}"
                )

        # Try standard locations
        standard_paths = [
            Path("infra/keycloak/credentials.yaml"),
            Path(__file__).parent / "credentials.yaml",
            Path("keycloak_credentials.yaml"),  # Legacy location
        ]

        for standard_path in standard_paths:
            if standard_path.exists():
                logger.info(f"Using credentials file: {standard_path}")
                return standard_path

        # Fall back to example file
        example_paths = [
            Path(__file__).parent / "credentials.yaml.example",
            Path("infra/keycloak/credentials.yaml.example"),
        ]
        
        for example_path in example_paths:
            if example_path.exists():
                logger.warning(
                    f"No credentials file found, using example file: {example_path}"
                )
                logger.warning(
                    " WARNING: Using example credentials! Copy to infra/keycloak/credentials.yaml and update for production."
                )
                return example_path

        # If nothing found, raise error
        raise FileNotFoundError(
            "No Keycloak credentials file found. Please create infra/keycloak/credentials.yaml "
            "from infra/keycloak/credentials.yaml.example"
        )

    def load(self) -> KeycloakCredentials:
        """Load and parse credentials file.

        Returns:
            Parsed credentials configuration

        Raises:
            FileNotFoundError: If credentials file not found
            ValueError: If credentials file is invalid
        """
        if self._credentials is not None:
            return self._credentials

        try:
            logger.info(f"Loading Keycloak credentials from: {self.credentials_path}")

            with open(self.credentials_path) as f:
                data = yaml.safe_load(f)

            if not data:
                raise ValueError("Credentials file is empty")

            # Parse and validate credentials
            self._credentials = KeycloakCredentials(**data)

            logger.info(
                f"Successfully loaded credentials: "
                f"{len(self._credentials.users)} users, "
                f"{len(self._credentials.roles)} roles, "
                f"{len(self._credentials.clients)} clients"
            )

            return self._credentials

        except FileNotFoundError as e:
            logger.error(f"Credentials file not found: {self.credentials_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in credentials file: {e}")
            raise ValueError(f"Invalid YAML in credentials file: {e}") from e
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            raise ValueError(f"Error loading credentials: {e}") from e

    def get_credentials(self) -> KeycloakCredentials:
        """Get loaded credentials (load if not already loaded).

        Returns:
            Parsed credentials configuration
        """
        if self._credentials is None:
            return self.load()
        return self._credentials

    def get_master_admin(self) -> MasterAdminCredentials:
        """Get master admin credentials."""
        return self.get_credentials().master_admin

    def get_realm_admin(self) -> RealmAdminCredentials:
        """Get realm admin credentials."""
        return self.get_credentials().realm_admin

    def get_clients(self) -> list[ClientConfig]:
        """Get client configurations."""
        return self.get_credentials().clients

    def get_roles(self) -> list[RoleConfig]:
        """Get role configurations."""
        return self.get_credentials().roles

    def get_users(self) -> list[UserConfig]:
        """Get user configurations."""
        return self.get_credentials().users

    def get_role_hierarchy(self) -> dict[str, RoleHierarchyConfig]:
        """Get role hierarchy configuration."""
        return self.get_credentials().role_hierarchy


# Global credentials loader instance
_credentials_loader: CredentialsLoader | None = None


def get_credentials_loader(
    credentials_path: str | Path | None = None,
) -> CredentialsLoader:
    """Get the global credentials loader instance.

    Args:
        credentials_path: Optional path to credentials file

    Returns:
        Global credentials loader instance
    """
    global _credentials_loader
    if _credentials_loader is None:
        _credentials_loader = CredentialsLoader(credentials_path)
    return _credentials_loader


def load_keycloak_credentials(
    credentials_path: str | Path | None = None,
) -> KeycloakCredentials:
    """Load Keycloak credentials from file.

    Args:
        credentials_path: Optional path to credentials file

    Returns:
        Parsed credentials configuration
    """
    loader = get_credentials_loader(credentials_path)
    return loader.load()

