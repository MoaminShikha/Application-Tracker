"""
Create the PostgreSQL database before init_db.py runs.
This script connects to the default 'postgres' database and creates 'job_tracker'.
"""
import psycopg2
from psycopg2 import sql, errors

# Connection to default postgres database (no job_tracker db needed yet)
conn_params = {
    'host': 'localhost',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres',
    'password': 'm0535266305'
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

