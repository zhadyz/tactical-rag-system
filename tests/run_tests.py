"""
Test Suite Runner
Convenient script to run different test categories
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd: list, description: str):
    """Run command and handle errors"""
    print(f"\n{'='*80}")
    print(f"{description}")
    print(f"{'='*80}\n")

    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)

    if result.returncode != 0:
        print(f"\n❌ {description} FAILED")
        return False
    else:
        print(f"\n✅ {description} PASSED")
        return True


def main():
    parser = argparse.ArgumentParser(description="Run Tactical RAG test suite")
    parser.add_argument(
        "category",
        nargs="?",
        default="all",
        choices=["all", "unit", "integration", "performance", "quick"],
        help="Test category to run"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--markers",
        "-m",
        type=str,
        help="Run tests matching given mark expression"
    )

    args = parser.parse_args()

    # Base pytest command
    base_cmd = ["pytest", "tests/"]

    # Add verbosity
    if args.verbose:
        base_cmd.append("-v")

    # Add coverage
    if args.coverage:
        base_cmd.extend(["--cov=_src", "--cov-report=html", "--cov-report=term"])

    success = True

    if args.category == "all":
        # Run all test categories in sequence
        print("Running complete test suite...")

        # Unit tests
        cmd = base_cmd + ["-m", "unit"]
        if not run_command(cmd, "Unit Tests"):
            success = False

        # Integration tests
        cmd = base_cmd + ["-m", "integration"]
        if not run_command(cmd, "Integration Tests"):
            success = False

        print("\nNote: Performance benchmarks should be run separately:")
        print("  python tests/performance/benchmark_vectordb.py")
        print("  python tests/performance/benchmark_scale.py")

    elif args.category == "quick":
        # Quick tests only (unit tests, no slow tests)
        cmd = base_cmd + ["-m", "unit and not slow"]
        success = run_command(cmd, "Quick Tests (Unit, Non-Slow)")

    elif args.category == "unit":
        cmd = base_cmd + ["-m", "unit"]
        success = run_command(cmd, "Unit Tests")

    elif args.category == "integration":
        cmd = base_cmd + ["-m", "integration"]
        success = run_command(cmd, "Integration Tests")

    elif args.category == "performance":
        print("Running performance benchmarks...")
        print("\nVector Database Benchmark:")
        if not run_command(
            ["python", "tests/performance/benchmark_vectordb.py"],
            "Vector DB Benchmark"
        ):
            success = False

        print("\nScale & Concurrency Benchmark:")
        if not run_command(
            ["python", "tests/performance/benchmark_scale.py"],
            "Scale Benchmark"
        ):
            success = False

    # Custom markers
    if args.markers:
        cmd = base_cmd + ["-m", args.markers]
        success = run_command(cmd, f"Tests with markers: {args.markers}")

    # Print summary
    print("\n" + "="*80)
    if success:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*80)

    # Show coverage report location if generated
    if args.coverage:
        print(f"\nCoverage report: {Path('htmlcov/index.html').absolute()}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
