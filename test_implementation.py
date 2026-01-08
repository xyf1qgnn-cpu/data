#!/usr/bin/env python3
"""
Test script for new polling and parallel processing features
"""

import os
import sys
import json
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import load_config, load_state, get_pending_directories, cleanup_directory, mark_directory_processed

def test_config_loading():
    """Test that config loads with new parameters"""
    print("\n=== Testing Config Loading ===")
    config = load_config()

    required_keys = [
        "polling_mode", "polling_source_path", "processed_dirs_location",
        "parallel_processing", "max_concurrent_files",
        "delete_excel_after_archive", "move_source_after_processing"
    ]

    all_present = True
    for key in required_keys:
        if key in config:
            print(f"  ✓ {key}: {config[key]}")
        else:
            print(f"  ✗ {key}: MISSING")
            all_present = False

    return all_present

def test_state_loading():
    """Test that state loads with new parameters"""
    print("\n=== Testing State Loading ===")
    state = load_state()

    required_keys = [
        "polling_processed_dirs", "current_processing_dir", "last_polling_check"
    ]

    all_present = True
    for key in required_keys:
        if key in state:
            print(f"  ✓ {key}: {state[key]}")
        else:
            print(f"  ✗ {key}: MISSING")
            all_present = False

    return all_present

def test_get_pending_directories():
    """Test getting pending directories"""
    print("\n=== Testing Get Pending Directories ===")

    # Create a test structure
    test_base = "/tmp/test_data_unextracted"
    os.makedirs(test_base, exist_ok=True)

    # Create test directories with PDFs
    test_dirs = ["database1", "database2", "database3"]
    for dir_name in test_dirs:
        dir_path = os.path.join(test_base, dir_name)
        os.makedirs(dir_path, exist_ok=True)

        # Create dummy PDF files
        for i in range(3):
            pdf_path = os.path.join(dir_path, f"test_{i}.pdf")
            with open(pdf_path, "w") as f:
                f.write("dummy pdf content")

    # Test with config
    config = load_config()
    config["polling_source_path"] = test_base

    state = load_state()
    state["polling_processed_dirs"] = []  # Reset for test

    pending = get_pending_directories(config, state)

    print(f"Found {len(pending)} pending directories:")
    for dir_info in pending:
        print(f"  - {dir_info['name']}: {dir_info['pdf_count']} PDFs")

    # Cleanup test data
    import shutil
    shutil.rmtree(test_base, ignore_errors=True)

    return len(pending) == 3

def test_state_management():
    """Test marking directories as processed"""
    print("\n=== Testing State Management ===")

    state = load_state()

    # Test marking a directory as processed
    test_dir_info = {
        "source_path": "/tmp/test_database",
        "name": "test_database"
    }

    initial_count = len(state.get("polling_processed_dirs", []))
    mark_directory_processed(test_dir_info, state)

    state = load_state()
    new_count = len(state.get("polling_processed_dirs", []))

    if new_count == initial_count + 1:
        print(f"  ✓ Directory marked as processed (count: {new_count})")
        return True
    else:
        print(f"  ✗ State not updated correctly (expected {initial_count + 1}, got {new_count})")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("CFST DATA EXTRACTION - FEATURE TEST SUITE")
    print("="*60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tests = [
        ("Config Loading", test_config_loading),
        ("State Loading", test_state_loading),
        ("Get Pending Directories", test_get_pending_directories),
        ("State Management", test_state_management)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print(f"{'='*60}")

    if passed == total:
        print("\n🎉 All tests passed! Implementation is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
