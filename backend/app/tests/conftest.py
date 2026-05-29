"""Pytest configuration and shared markers."""

import pytest

pytest_plugins = ["pytest_asyncio"]


def pytest_configure(config):  # noqa: ARG001
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "database: mark test as requiring database")
    config.addinivalue_line("markers", "migration: mark test as testing migrations")
    config.addinivalue_line("markers", "seeding: mark test as testing seeding")
    config.addinivalue_line("markers", "integration: mark test as integration test")


def pytest_collection_modifyitems(config, items):  # noqa: ARG001
    """Modify test collection to add markers."""
    for item in items:
        if "db_session" in item.fixturenames or "test_db_session" in item.fixturenames:
            item.add_marker(pytest.mark.database)

        if "migration" in item.name.lower():
            item.add_marker(pytest.mark.migration)

        if "seed" in item.name.lower():
            item.add_marker(pytest.mark.seeding)

        if "integration" in item.name.lower():
            item.add_marker(pytest.mark.integration)
