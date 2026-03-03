# Utility Scripts

This directory contains helper scripts for development and demonstration.

## verify_installation.py

Verifies that the application is properly installed and configured.

**Usage:**
```bash
python scripts/verify_installation.py
```

**What it checks:**
- All Python dependencies are installed
- Database connection works
- Required tables exist
- CLI commands are accessible

**When to use:**
- After initial installation
- When troubleshooting setup issues
- Before running the application for the first time
- After database configuration changes

## seed_data.py

Populates the database with realistic sample data for testing and demonstration.

**Usage:**
```bash
python scripts/seed_data.py
```

**What it creates:**
- 8 technology companies (Google, Microsoft, Amazon, Meta, etc.)
- 10 position types (Senior SWE, Mid-level, Staff, etc.)
- 3 recruiters with contact information
- 8 applications in various states:
  - Applied (recent submissions)
  - Interview Scheduled (upcoming conversations)
  - Interviewed (waiting for decisions)
  - Offer (active offers to consider)
  - Rejected (learning opportunities)
  - Withdrawn (changed priorities)

**When to use:**
- After initial database setup
- Before demonstrations
- For testing analytics features
- After schema changes (re-seed fresh data)

**Note:** This script requires an initialized database. Run `python -m job_tracker.database.init_db` first.

