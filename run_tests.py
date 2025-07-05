#!/usr/bin/env python3
"""
Test runner script for backtest-lab
This script provides different test execution options
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle output"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}:")
        print(f"Return code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"Error: Command not found. Make sure you have pytest installed.")
        print("Install with: pip install pytest pytest-cov pytest-mock")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test runner for backtest-lab")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "performance", "all", "quick", "coverage"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel"
    )
    parser.add_argument(
        "--failfast", "-x",
        action="store_true",
        help="Stop on first failure"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        base_cmd.append("-v")
    
    if args.failfast:
        base_cmd.append("-x")
    
    if args.parallel:
        base_cmd.extend(["-n", "auto"])
    
    # Test execution based on type
    success = True
    
    if args.type == "unit":
        cmd = base_cmd + [
            "tests/test_base.py",
            "tests/test_yahoo_provider.py",
            "tests/test_stock_loader.py",
            "tests/test_imports.py",
            "tests/test_edge_cases.py",
            "tests/test_configuration.py",
            "-m", "not integration and not network and not slow"
        ]
        success = run_command(cmd, "Unit Tests")
    
    elif args.type == "integration":
        cmd = base_cmd + [
            "tests/test_integration.py",
            "tests/test_end_to_end.py",
            "tests/test_examples.py",
            "-m", "integration"
        ]
        success = run_command(cmd, "Integration Tests")
    
    elif args.type == "performance":
        cmd = base_cmd + [
            "tests/test_performance.py",
            "-m", "slow"
        ]
        success = run_command(cmd, "Performance Tests")
    
    elif args.type == "quick":
        cmd = base_cmd + [
            "tests/",
            "-m", "not integration and not network and not slow",
            "--tb=short"
        ]
        success = run_command(cmd, "Quick Tests (no network/slow tests)")
    
    elif args.type == "coverage":
        cmd = base_cmd + [
            "tests/",
            "--cov=src/backtest_lab",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80",
            "-m", "not network and not slow"
        ]
        success = run_command(cmd, "Coverage Tests")
        
        if success:
            print("\nCoverage report generated in htmlcov/index.html")
    
    elif args.type == "all":
        # Run all test types in sequence
        test_suites = [
            (["tests/test_base.py", "-m", "not network"], "Base Classes Tests"),
            (["tests/test_yahoo_provider.py", "-m", "not network"], "Yahoo Provider Tests"),
            (["tests/test_stock_loader.py", "-m", "not network"], "Stock Loader Tests"),
            (["tests/test_imports.py", "-m", "not network"], "Import Tests"),
            (["tests/test_edge_cases.py", "-m", "not network"], "Edge Cases Tests"),
            (["tests/test_configuration.py", "-m", "not network"], "Configuration Tests"),
            (["tests/test_integration.py", "-m", "not network"], "Integration Tests"),
            (["tests/test_end_to_end.py", "-m", "not network"], "End-to-End Tests"),
            (["tests/test_examples.py", "-m", "not network"], "Examples Tests"),
        ]
        
        for test_args, description in test_suites:
            cmd = base_cmd + test_args
            suite_success = run_command(cmd, description)
            if not suite_success:
                success = False
                if args.failfast:
                    break
        
        # Summary
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        if success:
            print("✅ All test suites passed!")
        else:
            print("❌ Some test suites failed!")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
