#!/usr/bin/env python3
"""Test script to verify assassyn environment is properly set up."""

import sys
import os

def test_environment():
    print("=" * 60)
    print("Testing assassyn environment setup")
    print("=" * 60)

    # Check environment variables
    print("\n1. Checking environment variables:")
    assassyn_home = os.environ.get('ASSASSYN_HOME')
    pythonpath = os.environ.get('PYTHONPATH')

    if assassyn_home:
        print(f"   ✓ ASSASSYN_HOME: {assassyn_home}")
    else:
        print("   ✗ ASSASSYN_HOME not set")
        return False

    if pythonpath and 'assassyn' in pythonpath:
        print(f"   ✓ PYTHONPATH includes assassyn")
    else:
        print("   ✗ PYTHONPATH does not include assassyn")
        return False

    # Try importing assassyn
    print("\n2. Testing assassyn import:")
    try:
        import assassyn
        print(f"   ✓ assassyn imported successfully")
        print(f"   ✓ assassyn location: {assassyn.__file__}")
    except ImportError as e:
        print(f"   ✗ Failed to import assassyn: {e}")
        return False

    # Try importing main modules
    print("\n3. Testing module imports:")
    modules = ['frontend', 'backend', 'ir', 'utils']
    for module_name in modules:
        try:
            module = getattr(assassyn, module_name)
            print(f"   ✓ assassyn.{module_name} available")
        except AttributeError:
            print(f"   ✗ assassyn.{module_name} not available")

    print("\n" + "=" * 60)
    print("Environment test completed successfully!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_environment()
    sys.exit(0 if success else 1)
