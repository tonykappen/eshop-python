# Testing Guide

## Backend Tests

Backend tests live under `backend/app/tests/` and mirror the application structure:

```
app/tests/
├── conftest.py                    # Shared pytest markers
├── app/
│   ├── test_main.py               # Application entry point
│   ├── config/                    # Settings and DB config
│   ├── core/                      # Infrastructure (auth, cache, messaging, …)
│   └── modules/
│       ├── basket/
│       ├── catalog/
│       │   └── conftest.py        # Catalog-specific fixtures
│       └── ordering/
└── utils/
    └── mocks.py                   # Shared mock factories
```

### Running tests

```bash
cd backend
poetry run pytest app/tests/                  # all tests
poetry run pytest app/tests/app/modules/basket/  # one module
poetry run pytest -m database                 # database-marked tests only
```

### Markers

| Marker | Purpose |
|--------|---------|
| `database` | Tests using `test_db_session` or `db_session` fixtures |
| `migration` | Alembic migration tests |
| `seeding` | Database seeding tests |
| `integration` | Cross-layer integration tests |

Markers are registered in `conftest.py` and auto-applied based on fixture usage and test names.

### Shared mocks

```python
from app.tests.utils.mocks import MockKeycloakService, create_mock_settings
```

## Frontend Unit Tests

Frontend tests use **Jest** with **jsdom**. No E2E/browser tests are included.

```
frontend/
├── package.json
├── jest.config.js
└── tests/unit/
    ├── auth.test.js
    └── config.test.js
```

### Running tests

```bash
cd frontend
npm ci
npm test
```

### What's covered

| File | Tests |
|------|-------|
| `auth.test.js` | Token storage, auth headers, 401 handling, session validation |
| `config.test.js` | Default `APP_CONFIG` values, meta-tag overrides |

## Manual API Testing

Postman collections for manual exploration are in [tools/postman/](../tools/postman/).
