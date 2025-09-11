#!/usr/bin/env python3
"""
Test runner script for the Coworking Admin Panel application.
"""

import os
import subprocess
import sys


def run_tests():
    """Run the test suite using pytest."""
    print("Running tests for Coworking Admin Panel...")
    print("=" * 50)

    # Run pytest with coverage and verbose output
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"], check=True
        )

        print("\n" + "=" * 50)
        print("All tests passed successfully!")
        return True

    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 50)
        print("Some tests failed!")
        return False
    except FileNotFoundError:
        print("Error: pytest not found. Please install it with:")
        print("pip install pytest")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
