"""Database configuration for catalog module."""

from pydantic import Field
from pydantic_settings import BaseSettings


class CatalogDatabaseConfig(BaseSettings):
    """Database configuration for catalog module."""

    # Database connection
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/eshop",
        alias="CATALOG_DB_URL",
        description="Catalog database URL",
    )

    # Connection pool settings
    pool_size: int = Field(
        default=10,
        alias="CATALOG_DB_POOL_SIZE",
        description="Database connection pool size",
    )

    max_overflow: int = Field(
        default=20,
        alias="CATALOG_DB_MAX_OVERFLOW",
        description="Maximum overflow connections",
    )

    pool_timeout: int = Field(
        default=30,
        alias="CATALOG_DB_POOL_TIMEOUT",
        description="Pool timeout in seconds",
    )

    pool_recycle: int = Field(
        default=3600,
        alias="CATALOG_DB_POOL_RECYCLE",
        description="Pool recycle time in seconds",
    )

    # Connection settings
    echo: bool = Field(
        default=False, alias="CATALOG_DB_ECHO", description="Echo SQL statements"
    )

    echo_pool: bool = Field(
        default=False, alias="CATALOG_DB_ECHO_POOL", description="Echo pool events"
    )

    # Transaction settings
    isolation_level: str = Field(
        default="READ_COMMITTED",
        alias="CATALOG_DB_ISOLATION_LEVEL",
        description="Database isolation level",
    )

    # Migration settings
    migration_dir: str = Field(
        default="migrations",
        alias="CATALOG_MIGRATION_DIR",
        description="Migration directory",
    )

    # Schema settings
    schema_name: str = Field(
        default="catalog",
        alias="CATALOG_SCHEMA_NAME",
        description="Database schema name",
    )

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global configuration instance
catalog_db_config = CatalogDatabaseConfig()
