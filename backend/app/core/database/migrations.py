"""Database migration system using Alembic with per-module migrations."""

import asyncio
from pathlib import Path

from sqlalchemy import text

from app.core.database.session import AsyncSessionLocal
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


# Module configurations with their schema names
# Currently only catalog module is fully implemented
MODULE_CONFIGS = [
    {
        "name": "catalog",
        "path": "app/modules/catalog",
        "schema": "catalog",
    },
    # Basket and Ordering modules have placeholder migrations
    # Uncomment and implement when these modules are ready
    # {
    #     "name": "basket",
    #     "path": "app/modules/basket",
    #     "schema": "basket",
    # },
    # {
    #     "name": "ordering",
    #     "path": "app/modules/ordering",
    #     "schema": "ordering",
    # },
]


async def wait_for_database(max_retries: int = 30, delay: float = 2.0) -> None:
    """Wait for database to be ready."""
    logger.info("⏳ Waiting for database to be ready...")

    for attempt in range(max_retries):
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
                logger.info("✅ Database is ready!")
                return
        except Exception as e:
            if attempt < max_retries - 1:
                logger.debug(
                    f"Database not ready (attempt {attempt + 1}/{max_retries}): {e}"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"❌ Database failed to become ready after {max_retries} attempts"
                )
                raise


async def ensure_schemas_exist() -> None:
    """Ensure all required database schemas exist."""
    logger.info("🔧 Ensuring database schemas exist...")

    # Define all schemas that need to be created
    # Currently only catalog is active, keycloak is for auth service
    # basket and ordering schemas are placeholders for future implementation
    schemas = ["catalog", "keycloak"]

    try:
        async with AsyncSessionLocal() as session:
            for schema_name in schemas:
                logger.info(f"Creating schema: {schema_name}")
                await session.execute(
                    text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
                )

            # Create UUID extension if not exists
            await session.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))

            # Commit the changes
            await session.commit()

            logger.info("✅ All database schemas ensured successfully")

    except Exception as e:
        logger.error(f"❌ Failed to ensure schemas exist: {e}")
        raise


async def run_migrations() -> None:
    """Run database migrations for all modules using Alembic."""
    try:
        logger.info("🔄 Running database migrations...")

        # Ensure schemas exist first
        await ensure_schemas_exist()

        # Run migrations for each module
        for module_config in MODULE_CONFIGS:
            await run_module_migrations(module_config)

        logger.info("✅ All database migrations completed successfully")

    except Exception as e:
        logger.error(f"❌ Migration execution failed: {e}")
        raise


async def run_module_migrations(module_config: dict) -> None:
    """Run migrations for a specific module."""
    module_name = module_config["name"]
    module_path = Path(module_config["path"])
    schema_name = module_config["schema"]

    logger.info(
        f"🔄 Running migrations for module: {module_name} (schema: {schema_name})"
    )

    try:
        # Check if alembic configuration exists
        alembic_ini_path = module_path / "alembic.ini"
        if not alembic_ini_path.exists():
            logger.warning(
                f"⚠️ No alembic.ini found for module {module_name} at {alembic_ini_path}"
            )
            return

        # Check if migrations directory exists
        migrations_dir = module_path / "alembic"
        if not migrations_dir.exists():
            logger.warning(f"⚠️ No migrations directory found for module {module_name}")
            return

        # Run migrations using Alembic command
        process = await asyncio.create_subprocess_exec(
            "poetry",
            "run",
            "alembic",
            "-c",
            str(alembic_ini_path),
            "upgrade",
            "head",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=Path.cwd() / "backend",
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(
                f"❌ Migration execution failed for module {module_name}: {error_msg}"
            )
            # Don't raise here, continue with other modules
            logger.warning("⚠️ Continuing with other modules...")
        else:
            output = stdout.decode() if stdout else ""
            logger.debug(f"Migration output for {module_name}: {output}")
            logger.info(f"✅ Migrations completed for module: {module_name}")

    except Exception as e:
        logger.error(f"❌ Migration execution failed for module {module_name}: {e}")
        # Don't raise here, continue with other modules
        logger.warning("⚠️ Continuing with other modules...")


async def create_module_migration(module_name: str, message: str) -> None:
    """Create a new migration for a specific module."""
    module_config = next((m for m in MODULE_CONFIGS if m["name"] == module_name), None)

    if not module_config:
        logger.error(f"❌ Module {module_name} not found in MODULE_CONFIGS")
        raise ValueError(f"Module {module_name} not found")

    module_path = Path(module_config["path"])
    alembic_ini_path = module_path / "alembic.ini"

    if not alembic_ini_path.exists():
        logger.error(f"❌ No alembic.ini found for module {module_name}")
        raise FileNotFoundError(f"alembic.ini not found for module {module_name}")

    logger.info(f"📝 Creating migration for module {module_name}: {message}")

    try:
        process = await asyncio.create_subprocess_exec(
            "poetry",
            "run",
            "alembic",
            "-c",
            str(alembic_ini_path),
            "revision",
            "--autogenerate",
            "-m",
            message,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=Path.cwd() / "backend",
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(
                f"❌ Migration creation failed for module {module_name}: {error_msg}"
            )
            raise RuntimeError(
                f"Migration creation failed for {module_name}: {error_msg}"
            )

        output = stdout.decode() if stdout else ""
        logger.info(f"✅ Migration created for module {module_name}")
        logger.debug(f"Migration creation output: {output}")

    except Exception as e:
        logger.error(f"❌ Failed to create migration for module {module_name}: {e}")
        raise
