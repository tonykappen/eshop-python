# CI/CD Quick Reference Card

Quick commands and checklist for developers.

## 🚀 Before You Push

### Run All Checks Locally

```bash
cd backend
./scripts/ci-check.sh
```

### Individual Checks

```bash
# Format code (auto-fix)
poetry run black .
poetry run isort .
poetry run ruff format .

# Check formatting (no changes)
poetry run black --check .
poetry run isort --check-only .
poetry run ruff format --check .

# Linting
poetry run ruff check .              # Show issues
poetry run ruff check . --fix        # Auto-fix issues

# Type checking
poetry run mypy app --ignore-missing-imports --show-error-codes

# Security
poetry run bandit -r app

# Tests
poetry run pytest                                        # Run tests
poetry run pytest -v                                     # Verbose
poetry run pytest --cov=app                              # With coverage
poetry run pytest --cov=app --cov-report=html            # HTML report
poetry run pytest --cov=app --cov-fail-under=80          # Enforce 80%

# Pre-commit hooks
poetry run pre-commit run --all-files
```

## 📊 Coverage Commands

```bash
# Check current coverage
poetry run pytest --cov=app --cov-report=term-missing

# Generate HTML report
poetry run pytest --cov=app --cov-report=html
open htmlcov/index.html

# Find uncovered lines
poetry run pytest --cov=app --cov-report=term-missing | grep -v "100%"
```

## ✅ Pre-Push Checklist

- [ ] Code formatted with Black ✓
- [ ] Imports sorted with isort ✓
- [ ] Ruff linting passes ✓
- [ ] MyPy type checking passes ✓
- [ ] All tests pass ✓
- [ ] Coverage ≥80% ✓
- [ ] No security issues (Bandit) ✓
- [ ] Pre-commit hooks pass ✓

## 🔧 Common Fixes

### Fix formatting issues
```bash
poetry run black .
poetry run isort .
poetry run ruff format .
```

### Fix linting issues
```bash
poetry run ruff check . --fix
```

### Fix import issues
```bash
poetry run isort .
```

## 📝 Git Workflow

### Create feature branch
```bash
git checkout -b feature/your-feature-name
```

### Commit with proper message
```bash
git add .
git commit -m "feat(module): Add new feature description"
```

### Push and create PR
```bash
git push origin feature/your-feature-name
```

## 🎯 Commit Message Format

```
type(scope): Brief description

Longer description if needed

Fixes #123
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples:**
- `feat(catalog): Add product search`
- `fix(auth): Resolve token expiration`
- `test(orders): Add order creation tests`

## 🔍 Debugging CI Failures

### Coverage below 80%
```bash
# 1. Generate report
poetry run pytest --cov=app --cov-report=html

# 2. Open in browser
open htmlcov/index.html

# 3. Find uncovered files/lines (red/yellow)

# 4. Add tests for uncovered code

# 5. Verify
poetry run pytest --cov=app --cov-fail-under=80
```

### Linting failures
```bash
# See what's wrong
poetry run ruff check .

# Auto-fix
poetry run ruff check . --fix
poetry run black .
poetry run isort .
```

### Type checking errors
```bash
# Show errors with codes
poetry run mypy app --show-error-codes

# Common fixes:
# - Add type hints: def func() -> ReturnType:
# - Import types: from typing import List, Dict, Optional
# - Fix annotations: use correct types
```

### Test failures
```bash
# Run with verbose output
poetry run pytest -vvv

# Run specific test
poetry run pytest app/tests/test_file.py::test_function

# Run with debugging
poetry run pytest -vv --pdb

# Show print statements
poetry run pytest -s
```

## 📦 Setup Commands

### First time setup
```bash
cd backend
poetry install
poetry run pre-commit install
```

### Update dependencies
```bash
poetry update
poetry lock
```

### Update pre-commit hooks
```bash
poetry run pre-commit autoupdate
```

## 🌐 CI Status

### Check workflow status
Go to: `https://github.com/YOUR_ORG/YOUR_REPO/actions`

### Required checks that must pass:
- ✅ Code Quality Checks (Ruff, Black, isort)
- ✅ Security Checks (Bandit)
- ✅ Type Checking (MyPy)
- ✅ Tests with Coverage (≥80%)
- ✅ Quality Gate

## 🆘 Need Help?

- 📖 Full docs: [CONTRIBUTING.md](../CONTRIBUTING.md)
- 🔧 Setup guide: [CI_SETUP.md](CI_SETUP.md)
- 📋 Implementation details: [CI_CD_IMPLEMENTATION_SUMMARY.md](../CI_CD_IMPLEMENTATION_SUMMARY.md)
- 📚 Workflows: [workflows/README.md](workflows/README.md)

## 💡 Tips

1. **Run checks before committing**: Save time, catch issues early
2. **Use pre-commit hooks**: Automatic checks on every commit
3. **Write tests first**: TDD approach, easier to maintain 80% coverage
4. **Check coverage locally**: Don't wait for CI to fail
5. **Keep PRs small**: Easier to review, faster to merge
6. **Fix CI immediately**: Don't let broken builds accumulate

## 🔑 Key Paths

```
.github/
├── workflows/          # GitHub Actions workflows
├── ISSUE_TEMPLATE/     # Issue templates
├── labeler.yml         # Auto-labeling config
└── PULL_REQUEST_TEMPLATE.md

backend/
├── .pre-commit-config.yaml    # Pre-commit hooks
├── pyproject.toml             # Tool configurations
└── scripts/
    └── ci-check.sh            # Local CI script
```

## ⚡ One-Liner Shortcuts

```bash
# Full check before push
cd backend && ./scripts/ci-check.sh

# Quick format + lint fix
cd backend && poetry run black . && poetry run isort . && poetry run ruff check . --fix

# Test with coverage report
cd backend && poetry run pytest --cov=app --cov-report=html && open htmlcov/index.html

# Update and check everything
cd backend && poetry update && poetry run pre-commit run --all-files
```

---

**Print this page and keep it handy! 📄**

