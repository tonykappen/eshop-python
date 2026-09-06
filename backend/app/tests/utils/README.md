# Shared Test Utilities

This directory contains shared utilities for reducing test code duplication and improving test maintainability.

## Structure

```
tests/utils/
├── __init__.py          # Package initialization
├── mocks.py            # Shared mock objects and factories
└── README.md           # This documentation
```

## Usage

### Mock Utilities (`mocks.py`)

```python
from app.tests.utils.mocks import (
    MockKeycloakService,
    MockKeycloakUser,
    create_mock_settings,
    create_mock_async_client,
    create_mock_fastapi_keycloak
)

# Use in tests
mock_service = MockKeycloakService()
mock_user = MockKeycloakUser(sub="test-id", roles=["admin"])
```

## Benefits

1. **Reduced Duplication**: Common mock patterns are defined once
2. **Consistency**: All tests use the same mock structure
3. **Maintainability**: Changes to mocks only need to be made in one place
4. **Readability**: Tests focus on behavior, not setup

## Future Expansion

As we add more modules, we can expand these utilities:

- `db_mocks.py` - Database-related mocks
- `cache_mocks.py` - Cache-related mocks
- `messaging_mocks.py` - Message queue mocks
- `auth_mocks.py` - Authentication mocks (current)
