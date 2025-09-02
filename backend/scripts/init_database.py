#!/usr/bin/env python3
"""
Database initialization script for eShop
Handles migration creation, execution, and database setup
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from app.core.logging.logger import get_logger

logger = get_logger(__name__)


class DatabaseInitializer:
    """Handles database initialization and migration management."""

    def __init__(self):
        self.project_root = Path.cwd()
        self.migrations_dir = self.project_root / "migrations"
        self.versions_dir = self.migrations_dir / "versions"
        self.alembic_ini = self.project_root / "alembic.ini"

    async def initialize_database(self) -> None:
        """Main initialization method."""
        logger.info("🔧 Initializing eShop database...")

        try:
            # Ensure we're in the correct directory
            os.chdir(self.project_root)
            logger.debug(f"Working directory: {self.project_root}")

            # Create migrations directory if it doesn't exist
            await self._ensure_migrations_directory()

            # Create alembic.ini if it doesn't exist
            await self._ensure_alembic_config()

            # Create initial migration if none exist
            await self._create_initial_migration()

            # Run migrations
            await self._run_migrations()

            logger.info("✅ Database initialization completed successfully!")

        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise

    async def _ensure_migrations_directory(self) -> None:
        """Ensure migrations directory structure exists."""
        if not self.migrations_dir.exists():
            logger.info("📁 Creating migrations directory...")
            self.migrations_dir.mkdir(parents=True, exist_ok=True)

        if not self.versions_dir.exists():
            logger.info("📁 Creating versions directory...")
            self.versions_dir.mkdir(parents=True, exist_ok=True)

    async def _ensure_alembic_config(self) -> None:
        """Ensure alembic.ini exists."""
        if not self.alembic_ini.exists():
            logger.info("📝 Creating alembic.ini...")
            await self._run_command(["poetry", "run", "alembic", "init", "migrations"])

    async def _create_initial_migration(self) -> None:
        """Create initial migration if none exist."""
        # Check if there are any migration files
        migration_files = list(self.versions_dir.glob("*.py"))
        
        if not migration_files:
            logger.info("📝 Creating initial migration...")
            await self._run_command([
                "poetry", "run", "alembic", "revision", 
                "--autogenerate", "-m", "Initial migration"
            ])
        else:
            logger.info(f"📝 Found {len(migration_files)} existing migration(s)")

    async def _run_migrations(self) -> None:
        """Run all pending migrations."""
        logger.info("🔄 Running database migrations...")
        await self._run_command(["poetry", "run", "alembic", "upgrade", "head"])

    async def _run_command(self, command: list[str]) -> None:
        """Run a shell command and handle errors."""
        try:
            logger.debug(f"Running command: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                check=True
            )
            
            if result.stdout:
                logger.debug(f"Command output: {result.stdout}")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(command)}")
            logger.error(f"Error output: {e.stderr}")
            raise RuntimeError(f"Command execution failed: {e.stderr}")

    async def check_database_status(self) -> None:
        """Check the current database status."""
        logger.info("🔍 Checking database status...")
        
        try:
            # Check if alembic version table exists
            await self._run_command([
                "poetry", "run", "alembic", "current"
            ])
            
            logger.info("✅ Database status check completed")
            
        except Exception as e:
            logger.warning(f"Database status check failed: {e}")

    async def reset_database(self) -> None:
        """Reset the database (WARNING: This will delete all data)."""
        logger.warning("⚠️  Resetting database - this will delete all data!")
        
        try:
            # Drop all tables
            await self._run_command([
                "poetry", "run", "alembic", "downgrade", "base"
            ])
            
            # Remove migration files
            for migration_file in self.versions_dir.glob("*.py"):
                migration_file.unlink()
                logger.debug(f"Removed migration file: {migration_file}")
            
            # Recreate initial migration
            await self._create_initial_migration()
            await self._run_migrations()
            
            logger.info("✅ Database reset completed")
            
        except Exception as e:
            logger.error(f"❌ Database reset failed: {e}")
            raise


async def main():
    """Main entry point for the database initialization script."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        initializer = DatabaseInitializer()
        
        if command == "init":
            await initializer.initialize_database()
        elif command == "status":
            await initializer.check_database_status()
        elif command == "reset":
            await initializer.reset_database()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: init, status, reset")
            sys.exit(1)
    else:
        # Default to initialization
        initializer = DatabaseInitializer()
        await initializer.initialize_database()


if __name__ == "__main__":
    asyncio.run(main())


