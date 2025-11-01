"""Seed runner for executing seeds and recording in seed_version_catalog."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.seed.seed_registry import seed_registry

logger = logging.getLogger(__name__)


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
        logger.info("Starting seed execution")

        seeds = seed_registry.get_all_seeds()
        executed_count = 0

        for seed in seeds:
            try:
                if await self._is_seed_executed(seed.version):
                    logger.info(f"Seed {seed.version} already executed, skipping")
                    continue

                logger.info(f"Executing seed: {seed.version}")
                await seed.execute(self.session)
                await self._record_seed_execution(seed.version)
                executed_count += 1

                logger.info(f"Successfully executed seed: {seed.version}")

            except Exception as e:
                logger.error(f"Error executing seed {seed.version}: {e}")
                raise

        logger.info(f"Seed execution completed. Executed {executed_count} seeds.")

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
            logger.info(f"Seed {version} already executed, skipping")
            return

        logger.info(f"Executing seed: {version}")
        await seed.execute(self.session)
        await self._record_seed_execution(version)
        logger.info(f"Successfully executed seed: {version}")

    async def _is_seed_executed(self, version: str) -> bool:  # noqa: ARG002
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
        logger.info(f"Recorded seed execution: {version}")

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
        logger.warning("Resetting all seed executions")
        # In a real implementation, this would clear the seed_version_catalog table
        pass
