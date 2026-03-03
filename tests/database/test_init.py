"""
Quick test script to verify init_db works correctly.
Run this to test idempotent database initialization.
"""

from job_tracker.utils.logger import setup_logging
from job_tracker.database.init_db import InitDB

# Setup logging to see what happens
setup_logging(log_level="DEBUG", log_to_console=True)

print("=" * 60)
print("Testing Database Initialization")
print("=" * 60)

# First run - should create schema and seed data
print("\n[TEST 1] First initialization (should create tables + seed)...")
try:
    db_init = InitDB()
    db_init.initialize_database()
    print("✓ First initialization completed successfully")
except Exception as e:
    print(f"✗ First initialization failed: {e}")
    exit(1)

# Second run - should skip schema but still seed (idempotent)
print("\n[TEST 2] Second initialization (should skip tables, seed safely)...")
try:
    db_init2 = InitDB()
    db_init2.initialize_database()
    print("✓ Second initialization completed successfully")
except Exception as e:
    print(f"✗ Second initialization failed: {e}")
    exit(1)

# Verify tables exist
print("\n[TEST 3] Verifying tables exist...")
try:
    db_init3 = InitDB()
    missing = db_init3._get_missing_tables()
    if missing:
        print(f"✗ Missing tables: {missing}")
        exit(1)
    else:
        print("✓ All expected tables exist")
except Exception as e:
    print(f"✗ Table verification failed: {e}")
    exit(1)

print("\n" + "=" * 60)
print("All tests passed! Database initialization is idempotent.")
print("=" * 60)

