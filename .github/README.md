# GitHub CI/CD Configuration

This directory contains all GitHub Actions CI/CD workflows and templates for the eShop Python project.

## 📋 Quick Reference

### Run CI Checks Locally
```bash
cd backend
poetry install
poetry run black .
poetry run isort .
poetry run ruff check . --fix
poetry run mypy app --ignore-missing-imports
poetry run pytest --cov=app --cov-report=term-missing
```

---

## 🔄 CI Workflows

### Main CI Pipeline (`workflows/ci.yml`)

Runs on every pull request with **4 parallel jobs**:

1. **Code Quality Checks** 
   - Ruff linting
   - Black formatting
   - isort import sorting
   - Posts results as PR comment

2. **Security Checks**
   - Bandit security scanner
   - Posts findings as PR comment

3. **Type Checking**
   - MyPy static type analysis
   - Posts errors as PR comment

4. **Tests with Coverage**
   - Runs all 41 test files in `backend/app/tests/`
   - Tracks coverage (target: 80%)
   - Posts results as PR comment
   - Services: PostgreSQL, Redis, RabbitMQ

**All checks are informational - merge is never blocked! ✅**

---

## 💬 PR Comments

Each job posts a comment on PRs showing:
- ❌ Issues found with exact error messages
- 📋 Copy/paste commands to fix
- 🔗 Link to full CI logs
- ℹ️ "Informational only - not blocking merge"

---

## 🎯 Status: Non-Blocking

- ✅ All checks run on every PR
- ✅ Results posted as comments
- ✅ PRs can be merged anytime
- ✅ No blocking quality gates

---

## 📁 Structure

```
.github/
├── workflows/
│   ├── ci.yml              # Main CI pipeline
│   ├── code-quality.yml    # Code metrics
│   ├── pre-commit.yml      # Pre-commit hooks
│   └── status-checks.yml   # CI summary
│
├── ISSUE_TEMPLATE/
│   ├── bug_report.md       # Bug template
│   ├── feature_request.md  # Feature template
│   └── config.yml          # Template config
│
├── labeler.yml             # Auto-label PRs
├── PULL_REQUEST_TEMPLATE.md
├── QUICK_REFERENCE.md      # Developer commands
└── README.md               # This file
```

---

## ⚙️ Configuration

### Project Structure
- **Poetry project**: `backend/pyproject.toml`
- **Tests**: `backend/app/tests/` (41 files)
- **Application**: `backend/app/`

### CI Working Directory
All workflows run with `working-directory: ./backend`

---

## 🚀 For Developers

### First Time Setup
```bash
cd backend
poetry install
poetry run pre-commit install
```

### Before Pushing
```bash
cd backend
./scripts/ci-check.sh  # Run all checks locally
```

### Fix Issues
```bash
cd backend
poetry run black .
poetry run isort .
poetry run ruff check . --fix
poetry run pytest --cov=app
```

---

## 📊 What CI Checks

| Check | Tool | Blocks Merge? |
|-------|------|---------------|
| Linting | Ruff | ❌ No |
| Formatting | Black, Ruff | ❌ No |
| Import Sort | isort | ❌ No |
| Type Check | MyPy | ❌ No |
| Security | Bandit | ❌ No |
| Tests | pytest | ❌ No |
| Coverage | pytest-cov | ❌ No |

**Everything is informational!**

---

## 🔧 Troubleshooting

### If comments aren't appearing:
1. Check CI logs for "Could not read" errors
2. Ensure files are being created in backend/
3. Check GitHub Actions permissions

### If tests fail:
```bash
cd backend
poetry run pytest -vv  # Verbose output
```

### If dependencies fail:
```bash
cd backend
poetry lock  # Regenerate lock file
poetry install
```

---

## 📝 Recent Changes

- ✅ Consolidated to single Poetry project in `backend/`
- ✅ Removed duplicate root tests directory
- ✅ All checks made non-blocking
- ✅ Added PR comment reporting for all checks
- ✅ Poetry lock auto-fixes in CI

---

**Last Updated:** 2025-10-12  
**CI Status:** Non-blocking, informational reporting

