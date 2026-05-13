"""Data seeding system with 1-1 parity to .NET IDataSeeder."""

from abc import ABC, abstractmethod

from sqlalchemy import text

from app.core.database.session import AsyncSessionLocal
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


class IDataSeeder(ABC):
    """Base interface for data seeders - matches .NET IDataSeeder."""

    @abstractmethod
    async def seed_all_async(self) -> None:
        """Seed all data for this module - matches .NET SeedAllAsync()."""
        pass


class DataSeederManager:
    """Manages all data seeders with automatic execution at startup."""

    def __init__(self) -> None:
        self.seeders: list[type[IDataSeeder]] = []
        self.logger = BaseLogger(__name__)

    def register_seeder(self, seeder_class: type[IDataSeeder]) -> None:
        """Register a seeder class."""
        self.seeders.append(seeder_class)
        self.logger.debug(f"Registered seeder: {seeder_class.__name__}")

    async def run_all_seeders(self) -> None:
        """Run all registered seeders - matches .NET startup seeding."""
        if not self.seeders:
            self.logger.info("No seeders registered")
            return

        self.logger.info(f"Running {len(self.seeders)} data seeders...")

        async with AsyncSessionLocal():
            for seeder_class in self.seeders:
                try:
                    seeder = seeder_class()
                    await seeder.seed_all_async()
                    self.logger.info(f"[OK] Seeder {seeder_class.__name__} completed")
                except Exception as e:
                    self.logger.error(
                        f"[FAILED] Seeder {seeder_class.__name__} failed: {e}"
                    )
                    raise

        self.logger.info("[OK] All data seeders completed successfully")


# Global seeder manager instance
_seeder_manager = DataSeederManager()


def register_seeder(seeder_class: type[IDataSeeder]) -> None:
    """Register a seeder class - matches .NET DI registration pattern."""
    _seeder_manager.register_seeder(seeder_class)


async def run_seeding() -> None:
    """Run all registered seeders - called at application startup."""
    await _seeder_manager.run_all_seeders()


async def check_if_data_exists(table_name: str, schema: str = "public") -> bool:
    """Check if data exists in a table - used by seeders to avoid duplicate seeding."""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                text(f"SELECT COUNT(*) FROM {schema}.{table_name}")
            )
            count = result.scalar()
            return count is not None and count > 0
        except Exception as e:
            logger.warning(
                f"Could not check data existence for {schema}.{table_name}: {e}"
            )
            return False


async def ensure_schema_exists(schema_name: str) -> None:
    """Ensure a schema exists - used by seeders to create module schemas."""
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            await session.commit()
            logger.debug(f"Schema {schema_name} ensured")
        except Exception as e:
            logger.error(f"Failed to create schema {schema_name}: {e}")
            raise
