#!/usr/bin/env python3
"""Test runner script for Catalog module tests."""

import subprocess
import sys
from pathlib import Path


def run_tests(test_pattern="test_catalog*", verbose=True, coverage=False):
    """Run catalog module tests with specified options."""
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    backend_dir = project_root / "backend"
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test pattern
    cmd.append(f"app/tests/{test_pattern}")
    
    # Add verbosity
    if verbose:
        cmd.extend(["-v", "--tb=short"])
    
    # Add coverage if requested
    if coverage:
        cmd.extend([
            "--cov=app.modules.catalog",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    
    # Add other useful options
    cmd.extend([
        "--strict-markers",
        "--disable-warnings",
        "--color=yes"
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    print(f"Working directory: {backend_dir}")
    print("-" * 60)
    
    # Run the tests
    try:
        result = subprocess.run(cmd, cwd=backend_dir, check=True)
        print("\n" + "=" * 60)
        print("✅ All tests passed successfully!")
        return 0
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 60)
        print(f"❌ Tests failed with exit code {e.returncode}")
        return e.returncode
    except FileNotFoundError:
        print("❌ Error: pytest not found. Please install it with: pip install pytest")
        return 1


def run_specific_test_categories():
    """Run specific test categories."""
    
    test_categories = {
        "unit": "Unit tests for individual components",
        "integration": "Integration tests with database",
        "api": "API endpoint tests",
        "handlers": "Handler tests",
        "exceptions": "Exception handling tests",
        "contracts": "DTO and contract tests"
    }
    
    print("Available test categories:")
    for i, (key, description) in enumerate(test_categories.items(), 1):
        print(f"{i}. {key}: {description}")
    
    print("\nRunning all test categories...")
    
    # Run all catalog tests
    return run_tests("test_catalog*", verbose=True, coverage=True)


def main():
    """Main entry point for the test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Catalog module tests")
    parser.add_argument(
        "--pattern", 
        default="test_catalog*",
        help="Test pattern to run (default: test_catalog*)"
    )
    parser.add_argument(
        "--no-verbose", 
        action="store_true",
        help="Disable verbose output"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true",
        help="Run with coverage reporting"
    )
    parser.add_argument(
        "--categories", 
        action="store_true",
        help="Run specific test categories"
    )
    
    args = parser.parse_args()
    
    if args.categories:
        return run_specific_test_categories()
    else:
        return run_tests(
            test_pattern=args.pattern,
            verbose=not args.no_verbose,
            coverage=args.coverage
        )


if __name__ == "__main__":
    sys.exit(main())
