"""Alembic environment configuration for ordering module."""

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import your models here to ensure they're registered with Base
from app.modules.ordering.infrastructure.persistence.orm.orders.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
# Only access config when Alembic is actually running (context is available)
# When imported outside Alembic (e.g., during DI scanning), context.config won't exist
config = None
try:
    config = context.config
    # Interpret the config file for Python logging.
    # This line sets up loggers basically.
    if config and config.config_file_name is not None:
        fileConfig(config.config_file_name)
except AttributeError:
    # context.config is not available when module is imported outside of Alembic
    # This is expected during DI scanning, so we silently ignore it
    pass

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """Get database URL from settings or environment or config."""
    # Try to get from settings first (for consistency with app)
    try:
        from app.config.settings import settings
        return settings.database_connection_string
    except Exception:
        pass
    
    # Fallback to environment variable or config
    if config is None:
        # Fallback to environment variable if config not available
        return os.getenv(
            "ORDERING_DB_URL",
            os.getenv(
                "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/eshop"
            ),
        )
    return os.getenv("ORDERING_DB_URL", config.get_main_option("sqlalchemy.url"))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Ensure config is available
    global config
    if config is None:
        try:
            config = context.config
        except AttributeError:
            raise RuntimeError(
                "Alembic config is not available. Make sure migrations are run via Alembic CLI."
            )

    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="ordering",
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema="ordering",
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    # Ensure config is available
    global config
    if config is None:
        try:
            config = context.config
        except AttributeError:
            raise RuntimeError(
                "Alembic config is not available. Make sure migrations are run via Alembic CLI."
            )

    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Ensure the schema exists before running migrations
        await connection.execute(text("CREATE SCHEMA IF NOT EXISTS ordering"))
        await connection.commit()
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


# Only run migrations if Alembic context is properly initialized
# This prevents errors during module imports (e.g., DI scanning)
# Alembic will explicitly execute this code when running migrations
# We skip execution during normal imports to avoid proxy initialization errors
if config is not None:
    # Check if we're actually being called by Alembic (not just during import)
    # Alembic sets up the context before calling this module
    try:
        # This will fail if the proxy is not initialized
        is_offline = context.is_offline_mode()
        if is_offline:
            run_migrations_offline()
        else:
            run_migrations_online()
    except (AttributeError, RuntimeError) as e:
        # Only skip if it's a proxy initialization error (expected during imports)
        # Don't catch general exceptions here - let them propagate so migrations fail properly
        if "proxy" in str(e).lower() or "not initialized" in str(e).lower():
            pass
        else:
            raise
