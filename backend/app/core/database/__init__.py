"""Database package for eShop Modular Monolith."""

from app.core.database.base import Base
from app.core.database.session import create_db_engine, get_db_session

# Lazy imports to avoid import errors when Alembic runs
# These functions are only needed at runtime, not during migration imports
def __getattr__(name: str):
    """Lazy import for functions that might trigger problematic imports."""
    if name == "run_migrations":
        from app.core.database.migrations import run_migrations
        return run_migrations
    elif name == "run_seeding":
        from app.core.database.seeding import run_seeding
        return run_seeding
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "Base",
    "get_db_session",
    "create_db_engine",
    "run_migrations",
    "run_seeding",
]
