#!/usr/bin/env python3
"""
Quick verification that the application is properly installed and configured.

Run this after installation to verify:
- Python dependencies are installed
- Database connection works
- Tables exist
- CLI commands are accessible
"""

import sys
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
CHECKMARK = '✓'
CROSS = '✗'
WARNING = '⚠'


def check_dependencies():
    """Verify required packages are installed."""
    print("\n📦 Checking dependencies...")

    required = [
        'psycopg2',
        'click',
        'tabulate',
        'dotenv',
        'dateutil',
    ]

    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"  {GREEN}{CHECKMARK}{RESET} {package}")
        except ImportError:
            print(f"  {RED}{CROSS}{RESET} {package}")
            missing.append(package)

    if missing:
        print(f"\n{RED}Missing packages: {', '.join(missing)}{RESET}")
        print("Run: pip install -r requirements.txt")
        return False

    return True


def check_database_connection():
    """Verify database connection works."""
    print("\n🗄️  Checking database connection...")

    try:
        # Add project root to path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))

        from job_tracker.database.connection import DatabaseConnection
        from job_tracker.utils.config import get_connection_string

        conn_string = get_connection_string()

        with DatabaseConnection(conn_string) as db:
            if db.is_connected():
                print(f"  {GREEN}{CHECKMARK}{RESET} Connected to database")
                return True
            else:
                print(f"  {RED}{CROSS}{RESET} Not connected")
                return False

    except Exception as e:
        print(f"  {RED}{CROSS}{RESET} Connection failed: {e}")
        print(f"\n{YELLOW}Tip: Check your .env file or database credentials{RESET}")
        return False


def check_tables():
    """Verify required tables exist."""
    print("\n📋 Checking database tables...")

    try:
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))

        from job_tracker.database.connection import DatabaseConnection
        from job_tracker.database.query_executor import QueryExecutor
        from job_tracker.utils.config import get_connection_string

        conn_string = get_connection_string()

        required_tables = [
            'companies',
            'positions',
            'recruiters',
            'application_statuses',
            'applications',
            'application_events',
        ]

        with DatabaseConnection(conn_string) as db:
            executor = QueryExecutor(db)

            query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = %s
            """

            missing = []
            for table in required_tables:
                result = executor.execute_query_single(query, (table,))
                if result:
                    print(f"  {GREEN}{CHECKMARK}{RESET} {table}")
                else:
                    print(f"  {RED}{CROSS}{RESET} {table}")
                    missing.append(table)

            if missing:
                print(f"\n{YELLOW}Missing tables. Run: python -m job_tracker.database.init_db{RESET}")
                return False

            return True

    except Exception as e:
        print(f"  {RED}{CROSS}{RESET} Error checking tables: {e}")
        return False


def check_cli():
    """Verify CLI is accessible."""
    print("\n⚡ Checking CLI commands...")

    try:
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))

        from job_tracker.cli.main import cli

        print(f"  {GREEN}{CHECKMARK}{RESET} CLI module loaded")
        return True

    except Exception as e:
        print(f"  {RED}{CROSS}{RESET} Error loading CLI: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("🔍 Application Installation Verification")
    print("=" * 60)

    checks = [
        ("Dependencies", check_dependencies),
        ("Database Connection", check_database_connection),
        ("Database Tables", check_tables),
        ("CLI Commands", check_cli),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n{RED}Unexpected error in {name}: {e}{RESET}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = f"{GREEN}{CHECKMARK} PASS{RESET}" if result else f"{RED}{CROSS} FAIL{RESET}"
        print(f"  {status} - {name}")

    print(f"\n{passed}/{total} checks passed")

    if passed == total:
        print(f"\n{GREEN}✅ All checks passed! You're ready to go.{RESET}")
        print("\nNext steps:")
        print("  1. python scripts/seed_data.py  # Add sample data")
        print("  2. python -m job_tracker.cli menu  # Launch the app")
        return 0
    else:
        print(f"\n{RED}❌ Some checks failed. See above for details.{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

