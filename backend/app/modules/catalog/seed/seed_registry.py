"""Registry of seeds."""

import logging

from app.modules.catalog.seed.versions.catalog_seed_20250115_initial import (
    CatalogInitialSeed,
)

logger = logging.getLogger(__name__)


class Seed:
    """Base class for seeds."""

    def __init__(self, version: str, description: str):
        """
        Initialize the seed.

        Args:
            version: Seed version
            description: Seed description
        """
        self.version = version
        self.description = description

    async def execute(self, session) -> None:
        """
        Execute the seed.

        Args:
            session: Database session
        """
        raise NotImplementedError("Subclasses must implement execute method")


class SeedRegistry:
    """Registry for managing seeds."""

    def __init__(self):
        """Initialize the seed registry."""
        self._seeds: dict[str, Seed] = {}
        self._register_default_seeds()

    def _register_default_seeds(self) -> None:
        """Register default seeds."""
        # Register initial catalog seed
        initial_seed = CatalogInitialSeed()
        self.register_seed(initial_seed)

    def register_seed(self, seed: Seed) -> None:
        """
        Register a seed.

        Args:
            seed: Seed to register
        """
        if seed.version in self._seeds:
            logger.warning(f"Seed {seed.version} already registered, overwriting")

        self._seeds[seed.version] = seed
        logger.debug(f"Registered seed: {seed.version}")

    def get_seed(self, version: str) -> Seed | None:
        """
        Get a seed by version.

        Args:
            version: Seed version

        Returns:
            Seed if found, None otherwise
        """
        return self._seeds.get(version)

    def get_all_seeds(self) -> list[Seed]:
        """
        Get all registered seeds.

        Returns:
            List of all seeds
        """
        return list(self._seeds.values())

    def get_seeds_by_version(self, version_prefix: str) -> list[Seed]:
        """
        Get seeds by version prefix.

        Args:
            version_prefix: Version prefix to match

        Returns:
            List of matching seeds
        """
        return [
            seed
            for seed in self._seeds.values()
            if seed.version.startswith(version_prefix)
        ]

    def unregister_seed(self, version: str) -> None:
        """
        Unregister a seed.

        Args:
            version: Seed version to unregister
        """
        if version in self._seeds:
            del self._seeds[version]
            logger.debug(f"Unregistered seed: {version}")

    def clear_seeds(self) -> None:
        """Clear all registered seeds."""
        self._seeds.clear()
        logger.info("Cleared all seeds")

    def get_seed_summary(self) -> dict[str, str]:
        """
        Get summary of all seeds.

        Returns:
            Dictionary with seed versions and descriptions
        """
        return {seed.version: seed.description for seed in self._seeds.values()}


# Global seed registry instance
seed_registry = SeedRegistry()
