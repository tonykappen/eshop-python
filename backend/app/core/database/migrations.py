"""Database migration system using Alembic with per-module migrations."""

import asyncio
import os
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
    logger.info("Waiting for database to be ready...")

    for attempt in range(max_retries):
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
                logger.info("[OK] Database is ready!")
                return
        except Exception as e:
            if attempt < max_retries - 1:
                logger.debug(
                    f"Database not ready (attempt {attempt + 1}/{max_retries}): {e}"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"[FAILED] Database failed to become ready after {max_retries} attempts"
                )
                raise


async def ensure_schemas_exist() -> None:
    """Ensure all required database schemas exist (module schemas only)."""
    logger.info("[SETUP] Ensuring database schemas exist...")

    # Define all module schemas that need to be created
    # Currently only catalog is active
    # basket and ordering schemas are placeholders for future implementation
    # Keycloak schema is handled by infra/migrations
    schemas = ["catalog"]

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

            logger.info("[OK] All database schemas ensured successfully")

    except Exception as e:
        logger.error(f"[FAILED] Failed to ensure schemas exist: {e}")
        raise


async def run_migrations() -> None:
    """Run database migrations for all modules using Alembic."""
    try:
        logger.info("Running database migrations...")

        # Run infrastructure migrations first (Keycloak schema, etc.)
        # Import here to avoid import errors when Alembic runs
        from infra.migrations import run_infrastructure_migrations
        await run_infrastructure_migrations()

        # Ensure module schemas exist
        await ensure_schemas_exist()

        # Run migrations for each module
        for module_config in MODULE_CONFIGS:
            await run_module_migrations(module_config)

        logger.info("[OK] All database migrations completed successfully")

    except Exception as e:
        logger.error(f"[FAILED] Migration execution failed: {e}")
        raise


async def run_module_migrations(module_config: dict) -> None:
    """Run migrations for a specific module."""
    module_name = module_config["name"]
    module_path_str = module_config["path"]
    schema_name = module_config["schema"]

    logger.info(
        f"Running migrations for module: {module_name} (schema: {schema_name})"
    )

    try:
        # Determine backend directory (project root)
        # Try to find backend directory from current working directory
        cwd = Path.cwd()
        if (cwd / "backend").exists():
            backend_root = cwd / "backend"
        elif cwd.name == "backend":
            backend_root = cwd
        else:
            backend_root = cwd
        
        # Build absolute path to module directory
        module_path = backend_root / module_path_str
        
        # Check if alembic configuration exists
        alembic_ini_path = module_path / "alembic.ini"
        if not alembic_ini_path.exists():
            logger.warning(
                f"[WARNING] No alembic.ini found for module {module_name} at {alembic_ini_path}"
            )
            return

        # Check if migrations directory exists (could be "alembic" or "migrations")
        migrations_dir = module_path / "migrations"
        if not migrations_dir.exists():
            # Fallback to "alembic" for backwards compatibility
            migrations_dir = module_path / "alembic"
            if not migrations_dir.exists():
                logger.warning(f"[WARNING] No migrations directory found for module {module_name}")
                return
        
        # Check if versions directory exists
        versions_dir = migrations_dir / "versions"
        if not versions_dir.exists():
            logger.warning(
                f"[WARNING] No versions directory found for module {module_name} at {versions_dir}"
            )
            return
        
        # Run migrations using Alembic command
        # Set PYTHONPATH to include project root so both 'app' and 'infra' modules can be found
        env = dict(os.environ)
        project_root = backend_root.parent if backend_root.name == "backend" else backend_root
        pythonpath = str(project_root)
        if "PYTHONPATH" in env:
            # Use os.pathsep for cross-platform compatibility (; on Windows, : on Unix)
            pythonpath = f"{pythonpath}{os.pathsep}{env['PYTHONPATH']}"
        env["PYTHONPATH"] = pythonpath
        
        # Change working directory to module directory so script_location is resolved correctly
        # Alembic resolves script_location relative to cwd, not the config file location
        # Use relative path to alembic.ini since we're running from module_path
        alembic_ini_relative = "alembic.ini"
        process = await asyncio.create_subprocess_exec(
            "poetry",
            "run",
            "alembic",
            "-c",
            alembic_ini_relative,
            "upgrade",
            "head",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(module_path),
            env=env,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""
            
            # Combine both stdout and stderr for better error visibility
            error_msg = f"STDOUT: {stdout_str}\nSTDERR: {stderr_str}" if stdout_str or stderr_str else "Unknown error (no output captured)"
            
            logger.error(
                f"[FAILED] Migration execution failed for module {module_name}: {error_msg}"
            )
            # Don't raise here, continue with other modules
            logger.warning("[WARNING] Continuing with other modules...")
        else:
            output = stdout.decode("utf-8", errors="replace") if stdout else ""
            logger.debug(f"Migration output for {module_name}: {output}")
            logger.info(f"[OK] Migrations completed for module: {module_name}")

    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(
            f"[FAILED] Migration execution failed for module {module_name}: {e}\n"
            f"Traceback: {error_traceback}"
        )
        # Don't raise here, continue with other modules
        logger.warning("[WARNING] Continuing with other modules...")


async def create_module_migration(module_name: str, message: str) -> None:
    """Create a new migration for a specific module."""
    module_config = next((m for m in MODULE_CONFIGS if m["name"] == module_name), None)

    if not module_config:
        logger.error(f"[FAILED] Module {module_name} not found in MODULE_CONFIGS")
        raise ValueError(f"Module {module_name} not found")

    module_path = Path(module_config["path"])
    alembic_ini_path = module_path / "alembic.ini"

    if not alembic_ini_path.exists():
        logger.error(f"[FAILED] No alembic.ini found for module {module_name}")
        raise FileNotFoundError(f"alembic.ini not found for module {module_name}")

    logger.info(f"[CREATE] Creating migration for module {module_name}: {message}")

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
                f"[FAILED] Migration creation failed for module {module_name}: {error_msg}"
            )
            raise RuntimeError(
                f"Migration creation failed for {module_name}: {error_msg}"
            )

        output = stdout.decode() if stdout else ""
        logger.info(f"[OK] Migration created for module {module_name}")
        logger.debug(f"Migration creation output: {output}")

    except Exception as e:
        logger.error(f"[FAILED] Failed to create migration for module {module_name}: {e}")
        raise
