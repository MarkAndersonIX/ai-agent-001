#!/usr/bin/env python3
"""
Test runner script for AI Agent Base.

This script provides convenient commands for running different types of tests.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print("=" * 60)

    try:
        result = subprocess.run(command, check=True, capture_output=False)
        print(f"\n✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"\n❌ Command not found: {command[0]}")
        print("Make sure pytest is installed: pip install pytest")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run tests for AI Agent Base")
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=[
            "all",
            "unit",
            "integration",
            "tools",
            "api",
            "providers",
            "agents",
            "fast",
            "slow",
        ],
        help="Type of tests to run",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "-x", "--exitfirst", action="store_true", help="Stop on first failure"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Run with coverage report"
    )
    parser.add_argument(
        "--html-coverage", action="store_true", help="Generate HTML coverage report"
    )
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument(
        "--markers", action="store_true", help="Show available test markers"
    )

    args = parser.parse_args()

    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]

    # Add verbosity
    if args.verbose:
        base_cmd.append("-v")
    else:
        base_cmd.append("-q")

    # Add exit on first failure
    if args.exitfirst:
        base_cmd.append("-x")

    # Add parallel execution
    if args.parallel:
        base_cmd.extend(["-n", "auto"])

    # Add coverage
    if args.coverage or args.html_coverage:
        base_cmd.extend(["--cov=.", "--cov-report=term-missing"])
        if args.html_coverage:
            base_cmd.extend(["--cov-report=html"])

    # Show markers and exit
    if args.markers:
        cmd = base_cmd + ["--markers"]
        run_command(cmd, "Showing available test markers")
        return

    # Determine test paths and markers based on test type
    test_configs = {
        "all": {"paths": ["tests/"], "description": "All tests"},
        "unit": {
            "paths": ["tests/unit/"],
            "markers": ["-m", "unit or not integration"],
            "description": "Unit tests",
        },
        "integration": {
            "paths": ["tests/integration/"],
            "markers": ["-m", "integration"],
            "description": "Integration tests",
        },
        "tools": {
            "paths": ["tests/tools/"],
            "markers": ["-m", "tools or not integration"],
            "description": "Tool tests",
        },
        "api": {
            "paths": ["tests/integration/test_api_integration.py"],
            "markers": ["-m", "api"],
            "description": "API tests",
        },
        "providers": {"paths": ["tests/providers/"], "description": "Provider tests"},
        "agents": {
            "paths": ["tests/integration/test_agent_integration.py"],
            "description": "Agent tests",
        },
        "fast": {
            "paths": ["tests/"],
            "markers": ["-m", "not slow"],
            "description": "Fast tests (excluding slow tests)",
        },
        "slow": {
            "paths": ["tests/"],
            "markers": ["-m", "slow"],
            "description": "Slow tests only",
        },
    }

    config = test_configs.get(args.test_type)
    if not config:
        print(f"❌ Unknown test type: {args.test_type}")
        return False

    # Build final command
    cmd = base_cmd.copy()

    # Add markers if specified
    if "markers" in config:
        cmd.extend(config["markers"])

    # Add test paths
    cmd.extend(config["paths"])

    # Run the tests
    success = run_command(cmd, config["description"])

    if args.html_coverage and success:
        print(f"\n📊 Coverage report generated: htmlcov/index.html")

    return success


def check_dependencies():
    """Check if required test dependencies are installed."""
    required_packages = ["pytest", "pytest-cov"]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("❌ Missing required test dependencies:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall with: pip install " + " ".join(missing_packages))
        return False

    return True


def show_test_summary():
    """Show a summary of available test commands."""
    print("AI Agent Base Test Runner")
    print("=" * 40)
    print("\nAvailable test types:")
    print("  all          - Run all tests")
    print("  unit         - Run unit tests only")
    print("  integration  - Run integration tests only")
    print("  tools        - Run tool tests")
    print("  api          - Run API tests")
    print("  providers    - Run provider tests")
    print("  agents       - Run agent tests")
    print("  fast         - Run fast tests (exclude slow)")
    print("  slow         - Run slow tests only")

    print("\nUseful options:")
    print("  --verbose    - Detailed output")
    print("  --coverage   - Generate coverage report")
    print("  --html-coverage - Generate HTML coverage report")
    print("  --parallel   - Run tests in parallel")
    print("  --exitfirst  - Stop on first failure")
    print("  --markers    - Show available test markers")

    print("\nExamples:")
    print("  python run_tests.py unit --verbose")
    print("  python run_tests.py integration --coverage")
    print("  python run_tests.py fast --parallel")
    print("  python run_tests.py all --html-coverage")


if __name__ == "__main__":
    # Check if we're just showing help
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]):
        show_test_summary()
        sys.exit(0)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Run tests
    success = main()
    sys.exit(0 if success else 1)
