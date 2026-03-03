# Job Application Tracker

A PostgreSQL-backed CLI application for managing job applications with built-in analytics and status tracking.

## Features

- **Structured Application Management**: Track companies, positions, recruiters, and applications with relational integrity
- **Optional Job ID Tracking**: Store an external posting reference (LinkedIn, Greenhouse, Workday, etc.) per application
- **State Machine Validation**: Enforces valid status transitions (Applied → Interview → Offer, etc.)
- **Event Timeline**: Automatic logging of status changes and manual event tracking
- **Analytics Dashboard**: Conversion rates, response times, and status distribution metrics
- **Multiple Interfaces**: Interactive menu mode or direct CLI commands
- **Export Capabilities**: Generate reports in JSON or CSV format

## Architecture

This project demonstrates a layered architecture pattern:

```
┌─────────────────────────────────────┐
│   CLI Layer (Click + Tabulate)     │
├─────────────────────────────────────┤
│   Service Layer (Business Logic)   │
├─────────────────────────────────────┤
│   Model Layer (Data Validation)    │
├─────────────────────────────────────┤
│   Database Layer (Query Executor)  │
├─────────────────────────────────────┤
│   PostgreSQL (Relational Storage)  │
└─────────────────────────────────────┘
```

Key architectural decisions:
- **PostgreSQL over SQLite**: Demonstrates production-ready database interactions with proper connection management
- **Service Layer Pattern**: Separates business logic from data access and presentation
- **Dataclass Models**: Type-safe data structures with built-in validation
- **Context Managers**: Ensures proper resource cleanup for database connections

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design decisions.

## Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Virtual environment (recommended)

## Quick Start

### Easy Launch from Desktop (Windows)

For convenience, launcher scripts have been created on your Desktop:

- **Double-click** `run-job-tracker.bat` on your Desktop to launch the application
- Or right-click `run-job-tracker.ps1` → "Run with PowerShell"

### From PowerShell

Navigate to the project directory and activate your virtual environment:

```powershell
cd "C:\Users\kingm\OneDrive\Desktop\IDEs\Python Projects\Application-Tracker"
.venv\Scripts\Activate.ps1
python -m job_tracker.cli menu
```

### Want Sample Data?

Populate with sample applications first:

```powershell
python scripts/seed_data.py  # Creates 8 sample applications
python -m job_tracker.cli menu  # Launch interactive interface
```

This creates sample applications with various statuses (Applied, Interview Scheduled, Offer, Rejected, etc.)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/MoaminShikha/application-tracker.git
   cd application-tracker
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**
   
   Copy the example environment file and update with your PostgreSQL credentials:
   ```bash
   cp .env.example .env
   ```

5. **Initialize database**
   ```bash
   python -m job_tracker.database.init_db
   ```

6. **Verify installation (optional)**
   ```bash
   python scripts/verify_installation.py
   ```
   
   This checks that all dependencies are installed, database connection works, and tables exist.

## Quick Demo

### Menu Interface (Recommended)

```bash
python -m job_tracker.cli menu
```

This launches an interactive menu with numbered options and formatted tables.

### Direct Commands

```bash
# Add a company
python -m job_tracker.cli add-company --name "Google" --industry "Technology"

# Create an application
python -m job_tracker.cli add-application --company-id 1 --position-id 1 --job-id "GH-12345"

# View analytics
python -m job_tracker.cli analytics

# Export report
python -m job_tracker.cli export-report --format json --output report.json
```

Run `python -m job_tracker.cli --help` for all available commands.

## Project Structure

```
job_tracker/
├── analytics/          # Reporting and metrics calculation
├── cli/                # Command-line interface
├── database/           # Connection management and query execution
├── models/             # Data models with validation
├── services/           # Business logic layer
└── utils/              # Configuration and logging

tests/                  # Test suite organized by layer
docs/                   # Technical documentation
database_setup/         # Schema and initialization scripts
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=job_tracker

# Run specific test suite
pytest tests/services/
```


## Database Schema

The application uses a normalized relational schema with:
- Companies and positions (many-to-many via applications)
- Optional `applications.job_id` for external posting references
- Application status with transition validation
- Event logging for audit trail
- Recruiter contacts linked to companies

See [docs/SCHEMA.md](docs/SCHEMA.md) for the complete schema diagram.

## Roadmap

- [ ] Web interface using Flask/FastAPI
- [ ] Email notifications for follow-ups
- [ ] Calendar integration for interview scheduling
- [ ] Resume/cover letter attachment tracking
- [ ] Company research notes and links

