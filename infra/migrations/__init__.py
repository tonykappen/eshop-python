"""Infrastructure migrations for external services like Keycloak."""

from sqlalchemy import text

from app.core.database.session import AsyncSessionLocal
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


async def ensure_keycloak_schema() -> None:
    """Ensure Keycloak database schema exists."""
    logger.info("[SETUP] Ensuring Keycloak database schema exists...")

    try:
        async with AsyncSessionLocal() as session:
            logger.info("Creating schema: keycloak")
            await session.execute(text("CREATE SCHEMA IF NOT EXISTS keycloak"))

            # Commit the changes
            await session.commit()

            logger.info("[OK] Keycloak database schema ensured successfully")

    except Exception as e:
        logger.error(f"[FAILED] Failed to ensure Keycloak schema exists: {e}")
        raise


async def run_infrastructure_migrations() -> None:
    """Run all infrastructure-related migrations (schemas, extensions, etc.)."""
    logger.info("Running infrastructure migrations...")

    try:
        # Ensure Keycloak schema exists
        await ensure_keycloak_schema()

        logger.info("[OK] All infrastructure migrations completed successfully")

    except Exception as e:
        logger.error(f"[FAILED] Infrastructure migration execution failed: {e}")
        raise

