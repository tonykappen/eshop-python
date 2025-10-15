# Contributing to eShop Python

Thank you for your interest in contributing to eShop Python! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Quality Standards](#code-quality-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [CI/CD Pipeline](#cicd-pipeline)

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to maintain a welcoming and inclusive environment for all contributors.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/eshop-python.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.12 or higher
- Poetry for dependency management
- Docker and Docker Compose (for running services)

### Initial Setup

```bash
# Navigate to backend directory
cd backend

# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install

# Start infrastructure services
cd ..
docker-compose -f docker-compose.infrastructure.yml up -d

# Run database migrations
cd backend
poetry run alembic upgrade head
```

## Code Quality Standards

All contributions must meet the following quality standards:

### 1. Code Formatting

- **Black**: Line length 88, Python 3.12 target
- **isort**: Import sorting with Black profile
- **Ruff**: Fast Python linter and formatter

Run formatters:
```bash
poetry run black .
poetry run isort .
poetry run ruff format .
```

### 2. Linting

- **Ruff**: Comprehensive linting rules
  - Error detection (E, F)
  - Import conventions (I)
  - Naming conventions (N)
  - Code quality (B, C4, SIM)

Run linter:
```bash
poetry run ruff check . --fix
```

### 3. Type Checking

- **MyPy**: Static type checking
- All functions should have type hints
- Return types must be specified

Run type checker:
```bash
poetry run mypy app --ignore-missing-imports --show-error-codes
```

### 4. Security

- **Bandit**: Security vulnerability scanner
- No hardcoded secrets
- Proper input validation

Run security check:
```bash
poetry run bandit -r app
```

### 5. Pre-commit Hooks

Pre-commit hooks will automatically run before each commit:

```bash
# Run all hooks manually
poetry run pre-commit run --all-files
```

## Testing Requirements

### Coverage Requirement: 80% Minimum

All pull requests must maintain or improve the test coverage, with a **minimum of 80% coverage**.

### Running Tests

```bash
# Run all tests with coverage
poetry run pytest --cov=app --cov-report=term-missing

# Run specific test file
poetry run pytest app/tests/test_specific.py

# Run with coverage threshold check
poetry run pytest --cov=app --cov-fail-under=80
```

### Test Categories

- **Unit Tests**: Fast, isolated tests for individual functions/classes
- **Integration Tests**: Tests involving database, external services
- **Slow Tests**: Mark with `@pytest.mark.slow` and can be skipped in development

```python
import pytest

@pytest.mark.unit
def test_function():
    assert True

@pytest.mark.integration
async def test_database_operation():
    # Test with database
    pass

@pytest.mark.slow
def test_expensive_operation():
    # Long-running test
    pass
```

### Writing Good Tests

1. **Test file naming**: `test_*.py`
2. **Test function naming**: `test_*`
3. **Use fixtures**: For common setup and teardown
4. **Async tests**: Use `async def` and `pytest.mark.asyncio`
5. **Clear assertions**: Use descriptive error messages

Example:
```python
import pytest
from app.services import UserService

@pytest.mark.asyncio
async def test_create_user_success(db_session):
    """Test that creating a user with valid data succeeds."""
    service = UserService(db_session)
    user = await service.create_user(
        email="test@example.com",
        username="testuser"
    )
    assert user.id is not None
    assert user.email == "test@example.com"
```

## Pull Request Process

### Before Submitting

1. ✅ Ensure all tests pass
2. ✅ Run pre-commit hooks
3. ✅ Check code coverage (≥80%)
4. ✅ Update documentation if needed
5. ✅ Add tests for new features
6. ✅ Follow commit message conventions

### Commit Message Format

Use clear, descriptive commit messages:

```
type(scope): Brief description

Longer description if needed

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(catalog): Add product search functionality

fix(auth): Resolve token expiration issue

docs(api): Update API documentation for products endpoint

test(orders): Add tests for order creation
```

### Pull Request Template

When creating a pull request, provide:

1. **Description**: What does this PR do?
2. **Motivation**: Why is this change needed?
3. **Testing**: How was this tested?
4. **Screenshots**: If UI changes
5. **Checklist**: Complete the PR checklist

### Review Process

- PRs require at least one approval
- All CI checks must pass
- Address review comments
- Keep PRs focused and reasonably sized

## CI/CD Pipeline

All pull requests automatically run through our CI/CD pipeline:

### Automated Checks

1. **Code Quality Checks** ✅
   - Ruff linting
   - Black formatting
   - isort import ordering

2. **Security Checks** 🔒
   - Bandit security scanner
   - Dependency vulnerability scan

3. **Type Checking** 📝
   - MyPy static type analysis

4. **Tests** 🧪
   - Full test suite
   - **80% minimum coverage requirement**
   - PostgreSQL, Redis, RabbitMQ services

5. **Quality Gate** 🚦
   - All checks must pass
   - Coverage must be ≥80%

### Pipeline Status

You can monitor the status of your PR checks on GitHub:

- ✅ Green check: All tests passed
- ❌ Red X: Tests failed (click for details)
- 🟡 Yellow dot: Tests running

### Fixing CI Failures

If CI fails:

1. **Check the logs**: Click on the failed check
2. **Run locally**: Reproduce the issue
3. **Fix and push**: Update your branch
4. **Re-run if needed**: Use "Re-run jobs" if it was a flaky test

### Local CI Simulation

Run the same checks locally before pushing:

```bash
# Full check script
./scripts/ci-check.sh
```

Or individually:

```bash
# Formatting and linting
poetry run black --check .
poetry run isort --check-only .
poetry run ruff check .

# Type checking
poetry run mypy app --ignore-missing-imports

# Security
poetry run bandit -r app

# Tests with coverage
poetry run pytest --cov=app --cov-fail-under=80 -v

# Pre-commit hooks
poetry run pre-commit run --all-files
```

## Coverage Reports

After running tests, you can view the coverage report:

```bash
# Terminal report
poetry run pytest --cov=app --cov-report=term-missing

# HTML report (opens in browser)
poetry run pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Improving Coverage

If coverage is below 80%:

1. Check `htmlcov/index.html` for uncovered lines
2. Add tests for uncovered code
3. Remove dead code
4. Consider edge cases

## Branch Protection Rules

The `main` and `develop` branches are protected:

- ✅ Require pull request reviews
- ✅ Require status checks to pass (all CI jobs)
- ✅ Require branches to be up to date
- ✅ Require linear history
- ❌ No force pushes
- ❌ No direct commits

## Need Help?

- 📖 Check the [documentation](./README.md)
- 💬 Ask in discussions or issues
- 🐛 Report bugs with detailed information
- 💡 Suggest features with use cases

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for contributing to eShop Python! 🚀**

