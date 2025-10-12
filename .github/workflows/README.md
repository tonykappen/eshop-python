# GitHub Actions CI/CD Workflows

This directory contains GitHub Actions workflows for continuous integration and deployment.

## Workflows Overview

### 1. CI Pipeline (`ci.yml`)

The main CI pipeline that runs on every push and pull request. It includes:

#### Jobs:

- **lint-and-format**: Code quality checks
  - ✅ Ruff linter
  - ✅ Ruff format checker
  - ✅ Black format checker
  - ✅ isort import ordering

- **security**: Security scanning
  - ✅ Bandit security vulnerability scanner
  - 📄 Generates and uploads security report

- **type-check**: Static type checking
  - ✅ MyPy type checker with Python 3.12

- **test**: Test suite with coverage gate
  - ✅ Runs pytest with all tests
  - ✅ **80% minimum coverage requirement** (QUALITY GATE)
  - ✅ Spins up services: PostgreSQL, Redis, RabbitMQ
  - 📄 Generates HTML and XML coverage reports
  - 💬 Comments coverage on PRs
  - 📊 Uploads to Codecov

- **quality-gate**: Final check
  - ✅ Validates all previous jobs passed
  - ❌ Fails if any job failed

### 2. Code Quality (`code-quality.yml`)

Additional code quality metrics and checks:

- **code-metrics**: 
  - 📊 Ruff statistics
  - 📏 Lines of code count
  - 📝 Quality summary in GitHub Actions summary

- **dependency-review**: 
  - 🔍 Reviews dependency changes in PRs
  - ❌ Fails on moderate+ severity issues

- **pr-labeler**: 
  - 🏷️ Auto-labels PRs based on changed files

### 3. Pre-commit Checks (`pre-commit.yml`)

Runs pre-commit hooks configured in `.pre-commit-config.yaml`:

- ✅ All pre-commit hooks configured for the project
- 🔄 Caches pre-commit environments for speed

## Quality Gates

The CI enforces the following quality gates:

| Check | Tool | Requirement |
|-------|------|-------------|
| Linting | Ruff | Must pass |
| Formatting | Black + Ruff | Must pass |
| Import Order | isort | Must pass |
| Type Checking | MyPy | Must pass (with --ignore-missing-imports) |
| Security | Bandit | Reports generated (non-blocking) |
| Test Coverage | pytest-cov | **≥80% coverage required** |
| All Tests | pytest | Must pass |

## Coverage Requirement

The **minimum test coverage is set to 80%**. This is enforced via:

```bash
pytest --cov-fail-under=80
```

If coverage drops below 80%, the CI will fail and block merging.

## Service Dependencies

The test job automatically provisions:

- **PostgreSQL 15**: Database (port 5432)
- **Redis 7**: Caching (port 6379)
- **RabbitMQ 3**: Message queue (port 5672)

## Artifacts

The workflows generate and upload the following artifacts:

1. **bandit-security-report**: Security scan results (JSON)
2. **coverage-report**: HTML and XML coverage reports

Artifacts are retained for 30 days.

## Branch Triggers

- **Push**: `main`, `master`, `develop`, `docker-fixes`
- **Pull Request**: `main`, `master`, `develop`

## Required Secrets

Optional but recommended:

- `CODECOV_TOKEN`: For Codecov integration (public repos don't need this)

## Local Development

To run the same checks locally:

```bash
cd backend

# Linting
poetry run ruff check .
poetry run ruff format --check .
poetry run black --check .
poetry run isort --check-only .

# Type checking
poetry run mypy app --ignore-missing-imports

# Security
poetry run bandit -r app

# Tests with coverage
poetry run pytest --cov=app --cov-fail-under=80

# Pre-commit hooks
poetry run pre-commit run --all-files
```

## Pre-commit Setup

To install pre-commit hooks locally:

```bash
cd backend
poetry install
poetry run pre-commit install
```

This will run checks automatically before each commit.

## Troubleshooting

### Coverage Below 80%

If coverage fails:

1. Check the coverage report in the artifacts
2. Add tests for uncovered code
3. Review exclusions in `pyproject.toml`

### Linting Failures

Run locally to see details:
```bash
poetry run ruff check . --output-format=github
```

### Type Check Failures

MyPy is configured with strict settings in `pyproject.toml`. Common issues:

- Missing type hints
- Incorrect type annotations
- Missing return type annotations

### Service Connection Issues

If tests fail to connect to services, check:

- Service health checks in `ci.yml`
- Database URL in environment variables
- Port conflicts

## Badge Integration

Add these badges to your README.md:

```markdown
![CI](https://github.com/YOUR_ORG/YOUR_REPO/actions/workflows/ci.yml/badge.svg)
![Code Quality](https://github.com/YOUR_ORG/YOUR_REPO/actions/workflows/code-quality.yml/badge.svg)
[![codecov](https://codecov.io/gh/YOUR_ORG/YOUR_REPO/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_ORG/YOUR_REPO)
```

Replace `YOUR_ORG` and `YOUR_REPO` with your GitHub organization and repository names.

