"""Database migration system using Alembic with automatic execution."""

import subprocess
from pathlib import Path

from app.config.settings import settings
from app.core.logging.logger import get_logger

logger = get_logger(__name__)


def run_migrations() -> None:
    """Run database migrations using Alembic - matches .NET Entity Framework migrations."""
    try:
        logger.info("🔄 Running database migrations...")

        # Check if alembic.ini exists
        alembic_ini_path = Path("alembic.ini")
        if not alembic_ini_path.exists():
            logger.info("📝 Creating Alembic configuration...")
            _create_alembic_config()

        # Check if migrations directory exists
        migrations_dir = Path("migrations")
        if not migrations_dir.exists():
            logger.info("📁 Creating migrations directory...")
            _create_migrations_directory()

        # Run migrations
        result = subprocess.run(
            ["poetry", "run", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        if result.returncode == 0:
            logger.info("✅ Database migrations completed successfully")
            if result.stdout:
                logger.debug(f"Migration output: {result.stdout}")
        else:
            logger.error(f"❌ Database migrations failed: {result.stderr}")
            raise RuntimeError(f"Migration failed: {result.stderr}")

    except Exception as e:
        logger.error(f"❌ Migration execution failed: {e}")
        raise


def _create_alembic_config() -> None:
    """Create Alembic configuration file."""
    alembic_ini_content = f"""[alembic]
# path to migration scripts
script_location = migrations

# template used to generate migration file names; The default value is %%(rev)s_%%(slug)s
# Uncomment the line below if you want the files to be prepended with date and time
# file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# If specified, requires the python-dateutil library that can be
# installed by adding `alembic[tz]` to the pip requirements
# string value is passed to dateutil.tz.gettz()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version number format
version_num_format = %04d

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses
# os.pathsep. If this key is omitted entirely, it falls back to the legacy
# behavior of splitting on spaces and/or commas.
# Valid values for version_path_separator are:
#
# version_path_separator = :
# version_path_separator = ;
# version_path_separator = space
version_path_separator = os

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = {settings.database_connection_string}


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

# lint with attempts to fix using "ruff" - use the exec runner, execute a binary
# hooks = ruff
# ruff.type = exec
# ruff.executable = %(here)s/.venv/bin/ruff
# ruff.options = --fix REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""

    with open("alembic.ini", "w") as f:
        f.write(alembic_ini_content)


def _create_migrations_directory() -> None:
    """Create migrations directory structure."""
    # Create migrations directory
    migrations_dir = Path("migrations")
    migrations_dir.mkdir(exist_ok=True)

    # Create versions directory
    versions_dir = migrations_dir / "versions"
    versions_dir.mkdir(exist_ok=True)

    # Create env.py
    env_py_content = '''"""Alembic environment configuration."""

import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import all models to ensure they are registered with SQLAlchemy
from app.core.database.base import Base
from app.modules.catalog.infrastructure.orm_models import *
from app.modules.basket.infrastructure.orm_models import *
from app.modules.ordering.infrastructure.orm_models import *

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

    with open(migrations_dir / "env.py", "w") as f:
        f.write(env_py_content)

    # Create script.py.mako template
    script_mako_content = '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''

    with open(migrations_dir / "script.py.mako", "w") as f:
        f.write(script_mako_content)


def create_initial_migration() -> None:
    """Create initial migration for all models."""
    try:
        logger.info("📝 Creating initial migration...")

        result = subprocess.run(
            [
                "poetry",
                "run",
                "alembic",
                "revision",
                "--autogenerate",
                "-m",
                "Initial migration",
            ],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        if result.returncode == 0:
            logger.info("✅ Initial migration created successfully")
            if result.stdout:
                logger.debug(f"Migration creation output: {result.stdout}")
        else:
            logger.error(f"❌ Initial migration creation failed: {result.stderr}")
            raise RuntimeError(f"Migration creation failed: {result.stderr}")

    except Exception as e:
        logger.error(f"❌ Initial migration creation failed: {e}")
        raise
