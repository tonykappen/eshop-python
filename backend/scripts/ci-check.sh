#!/bin/bash

# Local CI Check Script
# This script runs all CI checks locally before pushing to GitHub
# Run from the backend directory: ./scripts/ci-check.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Error: pyproject.toml not found. Please run this script from the backend directory."
    exit 1
fi

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    print_error "Error: Poetry is not installed. Please install Poetry first."
    echo "Visit: https://python-poetry.org/docs/#installation"
    exit 1
fi

print_header "Starting Local CI Checks"

# Track if any checks failed
FAILED=0

# 1. Code Formatting Checks
print_header "1/7 Code Formatting (Black)"
if poetry run black --check . 2>&1; then
    print_success "Black formatting check passed"
else
    print_error "Black formatting check failed"
    echo "Run: poetry run black . (to fix)"
    FAILED=1
fi

# 2. Import Sorting
print_header "2/7 Import Sorting (isort)"
if poetry run isort --check-only . 2>&1; then
    print_success "isort check passed"
else
    print_error "isort check failed"
    echo "Run: poetry run isort . (to fix)"
    FAILED=1
fi

# 3. Ruff Linting
print_header "3/7 Linting (Ruff)"
if poetry run ruff check . 2>&1; then
    print_success "Ruff linting passed"
else
    print_error "Ruff linting failed"
    echo "Run: poetry run ruff check . --fix (to auto-fix)"
    FAILED=1
fi

# 4. Ruff Formatting
print_header "4/7 Formatting (Ruff)"
if poetry run ruff format --check . 2>&1; then
    print_success "Ruff format check passed"
else
    print_error "Ruff format check failed"
    echo "Run: poetry run ruff format . (to fix)"
    FAILED=1
fi

# 5. Type Checking
print_header "5/7 Type Checking (MyPy)"
if poetry run mypy app --ignore-missing-imports --show-error-codes 2>&1; then
    print_success "MyPy type checking passed"
else
    print_warning "MyPy type checking has issues (non-blocking)"
    # Don't fail on mypy for now as it's configured as continue-on-error in CI
fi

# 6. Security Checks
print_header "6/7 Security Scanning (Bandit)"
if poetry run bandit -r app -f screen 2>&1; then
    print_success "Bandit security check passed"
else
    print_warning "Bandit found potential security issues (non-blocking)"
    # Don't fail on bandit as it's informational in CI
fi

# 7. Tests with Coverage
print_header "7/7 Tests with Coverage (Pytest)"
print_warning "Note: This requires running database, Redis, and RabbitMQ services"
echo "Ensure services are running: docker-compose -f ../docker-compose.infrastructure.yml up -d"
echo ""

read -p "Do you want to run tests now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if poetry run pytest --cov=app --cov-report=term-missing --cov-fail-under=80 -v 2>&1; then
        print_success "All tests passed with ≥80% coverage"
    else
        print_error "Tests failed or coverage is below 80%"
        FAILED=1
    fi
else
    print_warning "Skipping tests (you should run them before pushing!)"
fi

# 8. Pre-commit Hooks (optional)
print_header "Pre-commit Hooks (Optional)"
read -p "Do you want to run pre-commit hooks? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if poetry run pre-commit run --all-files 2>&1; then
        print_success "Pre-commit hooks passed"
    else
        print_error "Pre-commit hooks failed"
        FAILED=1
    fi
fi

# Summary
print_header "Summary"

if [ $FAILED -eq 0 ]; then
    print_success "All CI checks passed! ✨"
    echo ""
    echo "Your code is ready to push! 🚀"
    echo ""
    echo "Next steps:"
    echo "  1. git add ."
    echo "  2. git commit -m 'Your commit message'"
    echo "  3. git push"
    exit 0
else
    print_error "Some CI checks failed! ❌"
    echo ""
    echo "Please fix the issues above before pushing."
    echo ""
    echo "Quick fixes:"
    echo "  • Formatting: poetry run black . && poetry run isort . && poetry run ruff format ."
    echo "  • Linting: poetry run ruff check . --fix"
    echo "  • Tests: poetry run pytest --cov=app --cov-report=term-missing"
    exit 1
fi

