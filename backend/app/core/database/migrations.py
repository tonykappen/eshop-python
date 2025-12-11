"""Database migration system using Alembic with per-module migrations."""

import asyncio
import os
import subprocess
from pathlib import Path

from sqlalchemy import text

from app.core.database.session import AsyncSessionLocal
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)

# ---------------------------------------------------------------------------
# Module configuration
# ---------------------------------------------------------------------------

MODULE_CONFIGS = [
    {
        "name": "catalog",
        "path": "app/modules/catalog",
        "schema": "catalog",
    },
    # Future modules (basket, ordering) can be added here
]


# ---------------------------------------------------------------------------
# Cross-platform subprocess helper
# ---------------------------------------------------------------------------

async def _run_subprocess(
    cmd: list[str],
    cwd: str | None = None,
    env: dict | None = None,
) -> tuple[int, str, str]:
    """
    Run a subprocess in a way that works on both Linux and Windows.

    Uses subprocess.run() in a worker thread via asyncio.to_thread(), so the
    event loop is not blocked, and we avoid platform-specific asyncio
    subprocess limitations (e.g., on Windows).
    """
    def _runner():
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout or "", result.stderr or ""

    return await asyncio.to_thread(_runner)


# ---------------------------------------------------------------------------
# Database readiness & schema creation
# ---------------------------------------------------------------------------

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

    # Currently only catalog is active; add more as modules are implemented
    schemas = ["catalog"]

    try:
        async with AsyncSessionLocal() as session:
            for schema_name in schemas:
                logger.info(f"Creating schema if not exists: {schema_name}")
                await session.execute(
                    text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
                )

            # Create UUID extension if not exists
            await session.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))

            await session.commit()
            logger.info("[OK] All database schemas ensured successfully")

    except Exception as e:
        logger.error(f"[FAILED] Failed to ensure schemas exist: {e}")
        raise


# ---------------------------------------------------------------------------
# Migration entrypoint
# ---------------------------------------------------------------------------

async def run_migrations() -> None:
    """Run database migrations for all modules using Alembic."""
    try:
        logger.info("Running database migrations...")

        # Run infrastructure migrations first (Keycloak schema, etc.)
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


# ---------------------------------------------------------------------------
# Per-module migrations
# ---------------------------------------------------------------------------

async def run_module_migrations(module_config: dict) -> None:
    """Run migrations for a specific module."""
    module_name = module_config["name"]
    module_path_str = module_config["path"]
    schema_name = module_config["schema"]

    logger.info(
        f"Running migrations for module: {module_name} (schema: {schema_name})"
    )

    try:
        # Determine backend directory (project root resolution)
        cwd = Path.cwd()
        if (cwd / "backend").exists():
            backend_root = cwd / "backend"
        elif cwd.name == "backend":
            backend_root = cwd
        else:
            backend_root = cwd

        # Absolute path to module directory
        module_path = backend_root / module_path_str

        # Check Alembic config
        alembic_ini_path = module_path / "alembic.ini"
        if not alembic_ini_path.exists():
            logger.warning(
                f"[WARNING] No alembic.ini found for module {module_name} at {alembic_ini_path}"
            )
            return

        # Check migrations directory - try multiple locations:
        # 1. Blueprint location: infrastructure/persistence/migrations/products/versions/
        # 2. Standard location: migrations/versions/ or alembic/versions/
        versions_dir = None
        use_blueprint_location = False
        
        # Try blueprint location first (infrastructure/persistence/migrations/products/versions/)
        blueprint_versions_dir = module_path / "infrastructure" / "persistence" / "migrations" / "products" / "versions"
        if blueprint_versions_dir.exists() and (blueprint_versions_dir / "versions").exists():
            versions_dir = blueprint_versions_dir / "versions"
            use_blueprint_location = True
            logger.info(f"Found blueprint migration location for {module_name}: {versions_dir}")
        else:
            # Try standard locations
            migrations_dir = module_path / "migrations"
            if not migrations_dir.exists():
                migrations_dir = module_path / "alembic"
                if not migrations_dir.exists():
                    logger.warning(
                        f"[WARNING] No migrations directory found for module {module_name}"
                    )
                    return
            
            # Check versions directory
            versions_dir = migrations_dir / "versions"
            if not versions_dir.exists():
                logger.warning(
                    f"[WARNING] No versions directory found for module {module_name} at {versions_dir}"
                )
                return

        # Prepare environment so Alembic can import project modules
        env = dict(os.environ)
        project_root = (
            backend_root.parent if backend_root.name == "backend" else backend_root
        )
        pythonpath = str(project_root)
        if "PYTHONPATH" in env and env["PYTHONPATH"]:
            pythonpath = f"{pythonpath}{os.pathsep}{env['PYTHONPATH']}"
        env["PYTHONPATH"] = pythonpath

        # Use alembic.ini at module root (it now points to the correct script_location)
        alembic_ini_path = module_path / "alembic.ini"
        alembic_cwd = str(module_path)
        alembic_config = "alembic.ini"  # relative to module_path

        # Run Alembic upgrade
        cmd = [
            "poetry",
            "run",
            "alembic",
            "-c",
            alembic_config,
            "upgrade",
            "head",
        ]

        returncode, stdout_str, stderr_str = await _run_subprocess(
            cmd,
            cwd=alembic_cwd,
            env=env,
        )

        if returncode != 0:
            error_msg = (
                f"STDOUT: {stdout_str}\nSTDERR: {stderr_str}"
                if stdout_str or stderr_str
                else "Unknown error (no output captured)"
            )
            logger.error(
                f"[FAILED] Migration execution failed for module {module_name}: {error_msg}"
            )
            logger.warning("[WARNING] Continuing with other modules...")
        else:
            if stdout_str:
                logger.debug(f"Migration output for {module_name}: {stdout_str}")
            logger.info(f"[OK] Migrations completed for module: {module_name}")

    except Exception as e:
        import traceback

        error_traceback = traceback.format_exc()
        logger.error(
            f"[FAILED] Migration execution failed for module {module_name}: {e}\n"
            f"Traceback: {error_traceback}"
        )
        logger.warning("[WARNING] Continuing with other modules...")


# ---------------------------------------------------------------------------
# Migration creation helper
# ---------------------------------------------------------------------------

async def create_module_migration(module_name: str, message: str) -> None:
    """Create a new migration for a specific module."""
    module_config = next((m for m in MODULE_CONFIGS if m["name"] == module_name), None)

    if not module_config:
        logger.error(f"[FAILED] Module {module_name} not found in MODULE_CONFIGS")
        raise ValueError(f"Module {module_name} not found")

    module_path_str = module_config["path"]

    # Determine backend directory (project root resolution)
    cwd = Path.cwd()
    if (cwd / "backend").exists():
        backend_root = cwd / "backend"
    elif cwd.name == "backend":
        backend_root = cwd
    else:
        backend_root = cwd

    # Absolute path to module directory
    module_path = backend_root / module_path_str
    alembic_ini_path = module_path / "alembic.ini"

    if not alembic_ini_path.exists():
        logger.error(f"[FAILED] No alembic.ini found for module {module_name}")
        raise FileNotFoundError(f"alembic.ini not found for module {module_name}")

    logger.info(f"[CREATE] Creating migration for module {module_name}: {message}")

    try:
        # Prepare environment so Alembic can import project modules
        env = dict(os.environ)
        project_root = (
            backend_root.parent if backend_root.name == "backend" else backend_root
        )
        pythonpath = str(project_root)
        if "PYTHONPATH" in env and env["PYTHONPATH"]:
            pythonpath = f"{pythonpath}{os.pathsep}{env['PYTHONPATH']}"
        env["PYTHONPATH"] = pythonpath

        # Run Alembic revision
        cmd = [
            "poetry",
            "run",
            "alembic",
            "-c",
            "alembic.ini",  # relative to module_path (cwd)
            "revision",
            "--autogenerate",
            "-m",
            message,
        ]

        returncode, stdout_str, stderr_str = await _run_subprocess(
            cmd,
            cwd=str(module_path),
            env=env,
        )

        if returncode != 0:
            error_msg = stderr_str or "Unknown error"
            logger.error(
                f"[FAILED] Migration creation failed for module {module_name}: {error_msg}"
            )
            raise RuntimeError(
                f"Migration creation failed for {module_name}: {error_msg}"
            )

        logger.info(f"[OK] Migration created for module {module_name}")
        if stdout_str:
            logger.debug(f"Migration creation output: {stdout_str}")

    except Exception as e:
        logger.error(
            f"[FAILED] Failed to create migration for module {module_name}: {e}"
        )
        raise
