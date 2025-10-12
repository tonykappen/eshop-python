# CI/CD Setup Guide

This guide explains how the CI/CD pipeline is configured and how to set it up for your repository.

## Overview

The CI/CD pipeline consists of multiple GitHub Actions workflows that ensure code quality, security, and test coverage for every pull request and commit.

## Workflows

### 1. Main CI Pipeline (`ci.yml`)

**Location:** `.github/workflows/ci.yml`

**Triggers:**
- Push to: `main`, `master`, `develop`, `docker-fixes`
- Pull requests to: `main`, `master`, `develop`

**Jobs:**
1. **lint-and-format**: Runs Ruff, Black, and isort
2. **security**: Runs Bandit security scanner
3. **type-check**: Runs MyPy type checker
4. **test**: Runs pytest with 80% coverage requirement
5. **quality-gate**: Ensures all previous jobs passed

### 2. Code Quality (`code-quality.yml`)

**Location:** `.github/workflows/code-quality.yml`

**Purpose:** Provides additional code metrics and dependency review

**Features:**
- Code statistics
- Lines of code count
- Dependency review (for PRs)
- Auto-labeling PRs

### 3. Pre-commit Checks (`pre-commit.yml`)

**Location:** `.github/workflows/pre-commit.yml`

**Purpose:** Runs all pre-commit hooks configured in `.pre-commit-config.yaml`

### 4. Status Checks (`status-checks.yml`)

**Location:** `.github/workflows/status-checks.yml`

**Purpose:** Provides a single status check for branch protection rules

## Setup Instructions

### Step 1: Copy Workflow Files

All workflow files are already in `.github/workflows/`:

```
.github/
├── workflows/
│   ├── ci.yml                 # Main CI pipeline
│   ├── code-quality.yml       # Code quality metrics
│   ├── pre-commit.yml         # Pre-commit hooks
│   └── status-checks.yml      # Combined status check
├── ISSUE_TEMPLATE/            # Issue templates
│   ├── bug_report.md
│   ├── feature_request.md
│   └── config.yml
├── labeler.yml                # PR auto-labeling config
└── PULL_REQUEST_TEMPLATE.md   # PR template
```

### Step 2: Enable GitHub Actions

1. Go to your repository on GitHub
2. Click **Settings** → **Actions** → **General**
3. Under **Actions permissions**, select:
   - ✅ "Allow all actions and reusable workflows"
4. Under **Workflow permissions**, select:
   - ✅ "Read and write permissions"
   - ✅ "Allow GitHub Actions to create and approve pull requests"
5. Click **Save**

### Step 3: Configure Branch Protection

Protect your main branches to require CI checks:

1. Go to **Settings** → **Branches**
2. Click **Add rule** or edit existing rule
3. Branch name pattern: `main` (or `master`, `develop`)
4. Enable the following:
   - ✅ **Require a pull request before merging**
     - ✅ Require approvals: 1
     - ✅ Dismiss stale pull request approvals when new commits are pushed
   - ✅ **Require status checks to pass before merging**
     - ✅ Require branches to be up to date before merging
     - Select these status checks:
       - `Code Quality Checks`
       - `Security Checks`
       - `Type Checking (MyPy)`
       - `Tests with Coverage`
       - `Quality Gate`
       - `All Required Checks Pass`
   - ✅ **Require conversation resolution before merging**
   - ✅ **Require linear history**
   - ✅ **Do not allow bypassing the above settings**
5. Click **Create** or **Save changes**

### Step 4: Configure Secrets (Optional)

For enhanced functionality, add these secrets:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add the following secrets:

#### Codecov (Optional for public repos)

- **Name:** `CODECOV_TOKEN`
- **Value:** Get from [codecov.io](https://codecov.io) after signing up
- **Purpose:** Upload coverage reports to Codecov

To get Codecov token:
1. Visit https://codecov.io
2. Sign in with GitHub
3. Select your repository
4. Copy the upload token
5. Add it as a GitHub secret

### Step 5: Test the Pipeline

1. Create a new branch:
   ```bash
   git checkout -b test-ci
   ```

2. Make a small change (e.g., add a comment to a file)

3. Commit and push:
   ```bash
   git add .
   git commit -m "test: Verify CI pipeline"
   git push origin test-ci
   ```

4. Create a pull request on GitHub

5. Watch the CI checks run in the PR

### Step 6: Local Development Setup

Set up pre-commit hooks locally:

```bash
cd backend

# Install dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install

# Test pre-commit hooks
poetry run pre-commit run --all-files
```

### Step 7: Run Local CI Checks

Before pushing, run all CI checks locally:

```bash
cd backend
./scripts/ci-check.sh
```

This script will run:
- Black formatting check
- isort import sorting
- Ruff linting
- Ruff formatting
- MyPy type checking
- Bandit security scan
- Pytest with coverage
- Pre-commit hooks (optional)

## Quality Gates

### Coverage Requirement: 80%

The pipeline enforces a minimum test coverage of 80%. This is configured in:

1. **pytest configuration** (`backend/pyproject.toml`):
   ```toml
   [tool.pytest.ini_options]
   addopts = [
       "--cov=app",
       "--cov-fail-under=80",
   ]
   ```

2. **CI workflow** (`ci.yml`):
   ```yaml
   - name: Run Tests with Coverage
     run: poetry run pytest --cov-fail-under=80
   ```

### How Coverage is Calculated

- **Target:** `app/` directory (main application code)
- **Excludes:** Test files, migrations, generated files
- **Threshold:** 80% line coverage

### Viewing Coverage Reports

#### In CI

1. Go to the failed/passed workflow run
2. Click on "Tests with Coverage" job
3. Expand the "Run Tests with Coverage" step
4. View coverage report in logs

#### Download HTML Report

1. Go to workflow run
2. Scroll to "Artifacts" section
3. Download `coverage-report`
4. Extract and open `htmlcov/index.html`

#### On Pull Requests

Coverage comments are automatically posted on PRs showing:
- Overall coverage percentage
- Coverage change from base branch
- Files with low coverage

## Troubleshooting

### Issue: CI fails with "Coverage below 80%"

**Solution:**
1. Download coverage report artifact
2. Open `htmlcov/index.html` to see uncovered lines
3. Add tests for uncovered code
4. Run locally: `poetry run pytest --cov=app --cov-report=html`

### Issue: Linting failures

**Solution:**
```bash
# Auto-fix most issues
poetry run black .
poetry run isort .
poetry run ruff check . --fix
poetry run ruff format .
```

### Issue: Type checking errors

**Solution:**
1. Add type hints to functions
2. Fix incorrect type annotations
3. Run: `poetry run mypy app --show-error-codes`

### Issue: Tests fail in CI but pass locally

**Possible causes:**
- Environment differences
- Missing environment variables
- Database state issues
- Timing issues (use proper async/await)

**Solution:**
1. Check CI logs for exact error
2. Ensure tests are isolated and repeatable
3. Use fixtures properly
4. Check database migrations are up to date

### Issue: Workflow doesn't trigger

**Possible causes:**
- Branch not configured in workflow triggers
- Actions disabled in repository settings
- Syntax error in workflow file

**Solution:**
1. Check `.github/workflows/*.yml` syntax
2. Verify branch names match
3. Enable Actions in repository settings

## Maintenance

### Updating Dependencies

When updating dependencies:

1. Update `pyproject.toml`
2. Run: `poetry lock`
3. Run: `poetry install`
4. Run CI checks locally
5. Update pre-commit hooks: `poetry run pre-commit autoupdate`
6. Test thoroughly before pushing

### Updating Workflow Actions

GitHub Actions should be updated regularly:

```yaml
# Check for newer versions
uses: actions/checkout@v4  # Update v3 → v4
uses: actions/setup-python@v5  # Update v4 → v5
```

### Monitoring CI Performance

- Check workflow run times regularly
- Optimize slow tests
- Use caching effectively
- Consider splitting large test suites

## Best Practices

### For Developers

1. ✅ Run `./scripts/ci-check.sh` before pushing
2. ✅ Install pre-commit hooks
3. ✅ Write tests for new features
4. ✅ Keep coverage above 80%
5. ✅ Fix CI failures promptly
6. ✅ Review coverage reports

### For Maintainers

1. ✅ Enforce branch protection rules
2. ✅ Require CI checks to pass
3. ✅ Monitor coverage trends
4. ✅ Review security scan results
5. ✅ Update dependencies regularly
6. ✅ Keep workflows up to date

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [pytest Documentation](https://docs.pytest.org/)
- [Pre-commit Documentation](https://pre-commit.com/)
- [Codecov Documentation](https://docs.codecov.com/)

## Support

If you encounter issues:

1. Check this documentation
2. Review workflow logs
3. Run checks locally
4. Check [CONTRIBUTING.md](../CONTRIBUTING.md)
5. Open an issue if problem persists

---

**CI/CD Pipeline Version:** 1.0  
**Last Updated:** 2025-10-12  
**Maintained by:** Development Team

