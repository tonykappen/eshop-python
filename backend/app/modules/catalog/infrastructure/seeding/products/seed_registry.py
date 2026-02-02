"""Registry of seeds."""

from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


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
        self._default_seeds_registered = False

    def _ensure_default_seeds_registered(self) -> None:
        """Lazily register default seeds to avoid circular imports."""
        if self._default_seeds_registered:
            return

        try:
            # Import here to avoid circular import
            from app.modules.catalog.infrastructure.seeding.products.versions.catalog_seed_20250115_initial import (
                CatalogInitialSeed,
            )

            # Register initial catalog seed
            initial_seed = CatalogInitialSeed()
            self.register_seed(initial_seed)
            self._default_seeds_registered = True
        except ImportError as e:
            # If import fails (e.g., during module scanning), we'll try again later
            logger.log_debug_with_context(
                "Could not register default seeds yet (will retry)",
                context={"error": str(e)}
            )

    def _register_default_seeds(self) -> None:
        """Register default seeds (deprecated - use _ensure_default_seeds_registered)."""
        self._ensure_default_seeds_registered()

    def register_seed(self, seed: Seed) -> None:
        """
        Register a seed.

        Args:
            seed: Seed to register
        """
        if seed.version in self._seeds:
            logger.log_warning_with_context(
                "Seed already registered, overwriting",
                context={"version": seed.version}
            )

        self._seeds[seed.version] = seed
        logger.log_debug_with_context(
            "Registered seed",
            context={"version": seed.version}
        )

    def get_seed(self, version: str) -> Seed | None:
        """
        Get a seed by version.

        Args:
            version: Seed version

        Returns:
            Seed if found, None otherwise
        """
        self._ensure_default_seeds_registered()
        return self._seeds.get(version)

    def get_all_seeds(self) -> list[Seed]:
        """
        Get all registered seeds.

        Returns:
            List of all seeds
        """
        self._ensure_default_seeds_registered()
        return list(self._seeds.values())

    def get_seeds_by_version(self, version_prefix: str) -> list[Seed]:
        """
        Get seeds by version prefix.

        Args:
            version_prefix: Version prefix to match

        Returns:
            List of matching seeds
        """
        self._ensure_default_seeds_registered()
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
        self._ensure_default_seeds_registered()
        if version in self._seeds:
            del self._seeds[version]
            logger.log_debug_with_context(
                "Unregistered seed",
                context={"version": version}
            )

    def clear_seeds(self) -> None:
        """Clear all registered seeds."""
        self._seeds.clear()
        self._default_seeds_registered = (
            False  # Reset flag so seeds can be re-registered
        )
        logger.log_with_context("Cleared all seeds")

    def get_seed_summary(self) -> dict[str, str]:
        """
        Get summary of all seeds.

        Returns:
            Dictionary with seed versions and descriptions
        """
        self._ensure_default_seeds_registered()
        return {seed.version: seed.description for seed in self._seeds.values()}


# Global seed registry instance
seed_registry = SeedRegistry()
