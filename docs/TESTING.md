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

### Production-only coverage

Coverage is scoped to production code only (`app/core`, `app/config`, `app/modules`, `app/main.py`). Test files under `app/tests/` are excluded.

```bash
cd backend
poetry run pytest app/tests/ --cov=app --cov-report=term --cov-report=html --cov-report=xml
open htmlcov/index.html   # local HTML report
```

Per-module coverage example:

```bash
poetry run pytest app/tests/app/modules/basket/ --cov=app/modules/basket --cov-report=term-missing
```

**Target:** ≥ 80% production line coverage (informational in CI — does not block merge).

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

Frontend unit tests use **Jest** with **jsdom**. Shared page logic lives in `frontend/js/` modules extracted from HTML pages.

**Setup (once):**

```bash
./scripts/setup-frontend-tests.sh
```

Or from `frontend/`: `npm run setup` (installs deps + Chromium; use the root script on Linux for system deps via `--with-deps`).

```
frontend/
├── auth.js
├── config.js
├── js/
│   ├── api-client.js
│   └── utils.js
├── jest.config.js
└── tests/unit/
    ├── auth.test.js
    ├── config.test.js
    └── utils.test.js
```

```bash
cd frontend
npm ci
npm test
npm test -- --coverage   # Jest line coverage (target ≥ 80%, informational in CI)
```

| File | Tests |
|------|-------|
| `auth.test.js` | Token storage, auth headers, 401 handling, session validation |
| `config.test.js` | Default `APP_CONFIG` values, meta-tag overrides |
| `utils.test.js` | Shared helpers (`escapeHtml`, JWT roles, basket subtotal, API client) |

## Frontend API Contract Tests

Validate backend response shapes and error codes. Uses Playwright's `request` fixture (no browser).

```
frontend/tests/api-contracts/
├── helpers.js
├── products-api.spec.js
├── basket-api.spec.js
├── orders-api.spec.js
└── errors-api.spec.js
```

**Prerequisite:** full stack running (`docker compose up -d --wait` from repo root).

```bash
cd frontend
npm ci
npx playwright install chromium
npm run test:api-contracts
```

## Frontend E2E Tests (Playwright)

Browser tests for the multi-page HTML/JS app.

### Functional scenario matrix

| Scenario | user | manager | admin | Spec |
|----------|------|---------|-------|------|
| Login / logout | ✓ | ✓ | ✓ | `e2e/auth.spec.js` |
| Browse / search / paginate products | ✓ | partial | partial | `e2e/products.spec.js` |
| Add / update / remove basket | ✓ | n/a | n/a | `e2e/basket.spec.js` |
| Checkout → orders | ✓ | n/a | n/a | `e2e/basket.spec.js`, `e2e/orders.spec.js` |
| RBAC UI controls | ✓ | ✓ | ✓ | `e2e/rbac.spec.js` |
| CRUD product (create/edit/delete) | n/a | ✓ | ✓ | `e2e/manager-crud.spec.js` |
| Session expired / invalid token UX | ✓ | ✓ | ✓ | `e2e/session-expired.spec.js` |
| API error responses (401/404/422) | ✓ | ✓ | ✓ | `tests/api-contracts/errors-api.spec.js` |

**Target:** ≥ 80% of matrix cells covered by E2E + API contract tests (informational).

```
frontend/e2e/
├── helpers/
│   ├── auth.js
│   ├── checkout.js
│   └── constants.js
├── auth.spec.js
├── products.spec.js
├── basket.spec.js
├── orders.spec.js
├── rbac.spec.js
├── manager-crud.spec.js
└── session-expired.spec.js
```

**Prerequisite:** full stack running.

```bash
cd frontend
npm ci
npx playwright install chromium
npm run test:e2e
npm run test:e2e:report   # open playwright-report/index.html locally
npm run test:e2e:ui       # interactive UI mode
npm run test:all          # unit + API contracts + E2E
```

### Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `E2E_BASE_URL` | `http://localhost:3000` | Frontend base URL |
| `E2E_API_URL` | `http://localhost:8000` | Backend API URL |
| `E2E_USER_PASSWORD` | `changeme123` | Test user password (matches Keycloak example config) |
| `PLAYWRIGHT_SKIP_GLOBAL_SETUP` | unset | Set to `1` to skip health/auth waits |

`global-setup.js` polls backend `/health`, frontend `/`, auth-proxy, and seeded products before tests run.

## CI artifacts (informational)

Pull-request CI uploads reports as artifacts (non-blocking):

| Artifact | Job | Contents |
|----------|-----|----------|
| `coverage-report` | Backend tests | `backend/coverage.xml`, `backend/htmlcov/` |
| `jest-coverage-report` | Frontend unit tests | `frontend/coverage/` |
| `playwright-api-report` | API contract tests | `frontend/playwright-report/` |
| `playwright-e2e-report` | E2E tests | `frontend/playwright-report/`, `frontend/test-results/` |

Download artifacts from the GitHub Actions run summary. Open `htmlcov/index.html`, `coverage/lcov-report/index.html`, or `playwright-report/index.html` locally after extracting.

## Manual API Testing

Postman collections for manual exploration are in [tools/postman/](../tools/postman/).
