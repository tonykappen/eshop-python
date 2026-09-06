"""Alembic environment for Basket module."""

from logging.config import fileConfig

from alembic import context
from app.config.settings import settings
# Import the Base and ORM models for this module
from app.core.database.base import Base
from app.modules.basket.infrastructure.orm_models import *  # noqa: F401, F403
from sqlalchemy import engine_from_config, pool, text

# this is the Alembic Config object
# Only access config when Alembic is actually running (context is available)
# When imported outside Alembic (e.g., during DI scanning), context.config won't exist
config = None
try:
    config = context.config
    # Interpret the config file for Python logging
    if config and config.config_file_name is not None:
        fileConfig(config.config_file_name)
    # Set the SQLAlchemy URL from settings
    # Convert async URL to sync URL for Alembic migrations
    if config:
        db_url = settings.database_connection_string
        # Convert postgresql+asyncpg:// to postgresql+psycopg2:// for synchronous migrations
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        config.set_main_option("sqlalchemy.url", db_url)
except AttributeError:
    # context.config is not available when module is imported outside of Alembic
    # This is expected during DI scanning, so we silently ignore it
    pass

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# Module-specific schema
MODULE_SCHEMA = "basket"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    assert config is not None, "Alembic config must be available for migrations"
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=MODULE_SCHEMA,
        include_schemas=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def include_object(object, _name, type_, _reflected, _compare_to):
    """Filter objects to only include those in the module's schema."""
    if type_ == "table":
        # Only include tables in this module's schema
        return object.schema == MODULE_SCHEMA
    return True


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    assert config is not None, "Alembic config must be available for migrations"
    connectable = engine_from_config(
        config.get_section(config.config_ini_section) or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Ensure the schema exists before running migrations
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {MODULE_SCHEMA}"))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=MODULE_SCHEMA,
            include_schemas=True,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


# Only run migrations if Alembic context is properly initialized
# This prevents errors during module imports (e.g., DI scanning)
# Alembic will explicitly execute this code when running migrations
# We skip execution during normal imports to avoid proxy initialization errors
try:
    # Only try to run migrations if we can safely access the context
    # If config exists and is accessible, we're being run by Alembic
    if config is not None:
        # Double-check that context methods are accessible before calling them
        try:
            # This will fail if the proxy is not initialized
            is_offline = context.is_offline_mode()
            if is_offline:
                run_migrations_offline()
            else:
                run_migrations_online()
        except (AttributeError, RuntimeError, Exception):
            # Proxy not ready, skip migrations
            pass
except (AttributeError, RuntimeError, Exception):
    # If any error occurs (context not initialized, proxy not ready, etc.), skip migrations
    # This is expected when the module is imported outside of Alembic (e.g., during DI scanning)
    pass
