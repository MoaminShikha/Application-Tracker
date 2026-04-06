"""
Create the PostgreSQL database before init_db.py runs.
This script connects to the default 'postgres' database and creates 'job_tracker'.
"""
import os
import psycopg2
from psycopg2 import sql, errors
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')

conn_params = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': 'postgres',
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
}

try:
    print("Connecting to PostgreSQL server...")
    conn = psycopg2.connect(**conn_params)
    conn.autocommit = True

    cursor = conn.cursor()

    # Check if database exists
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'job_tracker'")
    exists = cursor.fetchone()

    if exists:
        print("✓ Database 'job_tracker' already exists")
    else:
        print("Creating database 'job_tracker'...")
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier('job_tracker')
        ))
        print("✓ Database 'job_tracker' created successfully")

    cursor.close()
    conn.close()
    print("✓ Database setup complete. You can now run init_db.py")

except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

