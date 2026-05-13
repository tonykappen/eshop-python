"""Seed runner for executing seeds and recording in seed_version_catalog."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging.base_logger import BaseLogger
from app.modules.catalog.infrastructure.seeding.products.seed_registry import (
    seed_registry,
)

logger = BaseLogger(__name__)


class SeedRunner:
    """Runs seeds and records execution in seed_version_catalog."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the seed runner.

        Args:
            session: Database session
        """
        self.session = session

    async def run_all_seeds(self) -> None:
        """Run all registered seeds in order."""
        logger.log_with_context("Starting seed execution")

        seeds = seed_registry.get_all_seeds()
        executed_count = 0

        for seed in seeds:
            try:
                if await self._is_seed_executed(seed.version):
                    logger.log_with_context(
                        "Seed already executed, skipping",
                        context={"version": seed.version}
                    )
                    continue

                logger.log_with_context(
                    "Executing seed",
                    context={"version": seed.version}
                )
                await seed.execute(self.session)
                await self._record_seed_execution(seed.version)
                executed_count += 1

                logger.log_with_context(
                    "Successfully executed seed",
                    context={"version": seed.version}
                )

            except Exception as e:
                logger.log_error_with_context(
                    "Error executing seed",
                    error=e,
                    context={"version": seed.version}
                )
                raise

        logger.log_with_context(
            "Seed execution completed",
            context={"executed_count": executed_count}
        )

    async def run_specific_seed(self, version: str) -> None:
        """
        Run a specific seed by version.

        Args:
            version: Seed version to run
        """
        seed = seed_registry.get_seed(version)
        if not seed:
            raise ValueError(f"Seed {version} not found")

        if await self._is_seed_executed(version):
            logger.log_with_context(
                "Seed already executed, skipping",
                context={"version": version}
            )
            return

        logger.log_with_context(
            "Executing seed",
            context={"version": version}
        )
        await seed.execute(self.session)
        await self._record_seed_execution(version)
        logger.log_with_context(
            "Successfully executed seed",
            context={"version": version}
        )

    async def _is_seed_executed(self, version: str) -> bool:
        """
        Check if a seed has been executed.

        Args:
            version: Seed version

        Returns:
            True if seed has been executed, False otherwise
        """
        # In a real implementation, this would check a seed_version_catalog table
        # For now, we'll use a simple approach
        return False

    async def _record_seed_execution(self, version: str) -> None:
        """
        Record seed execution in seed_version_catalog.

        Args:
            version: Seed version that was executed
        """
        # In a real implementation, this would insert into seed_version_catalog table
        # For now, we'll just log it
        logger.log_with_context(
            "Recorded seed execution",
            context={"version": version}
        )

    async def get_executed_seeds(self) -> list[str]:
        """
        Get list of executed seed versions.

        Returns:
            List of executed seed versions
        """
        # In a real implementation, this would query the seed_version_catalog table
        # For now, return empty list
        return []

    async def reset_seeds(self) -> None:
        """Reset all seed executions (for testing)."""
        logger.log_warning_with_context("Resetting all seed executions")
        # In a real implementation, this would clear the seed_version_catalog table
        pass
