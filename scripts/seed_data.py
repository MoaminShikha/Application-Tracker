#!/usr/bin/env python3
"""
Seed database with realistic sample data for demonstration purposes.

This script populates the database with example companies, positions,
applications, and events to showcase the application's functionality.
"""

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from job_tracker.services import (
    CompanyService,
    PositionService,
    RecruiterService,
    ApplicationService,
    EventService,
    StatusService,
)


def seed_data():
    """Populate database with realistic sample data."""

    print("🌱 Seeding database with sample data...\n")

    company_svc = CompanyService()
    position_svc = PositionService()
    recruiter_svc = RecruiterService()
    app_svc = ApplicationService()
    event_svc = EventService()
    status_svc = StatusService()

    def status_id(name: str) -> int:
        sid = status_svc.get_status_id_by_name(name)
        if sid is None:
            raise ValueError(f"Required status '{name}' not found in application_statuses")
        return sid

    # Companies
    print("📋 Creating companies...")
    companies = [
        {"name": "Google", "industry": "Technology", "location": "Mountain View, CA"},
        {"name": "Microsoft", "industry": "Technology", "location": "Redmond, WA"},
        {"name": "Amazon", "industry": "E-commerce", "location": "Seattle, WA"},
        {"name": "Meta", "industry": "Social Media", "location": "Menlo Park, CA"},
        {"name": "Apple", "industry": "Technology", "location": "Cupertino, CA"},
        {"name": "Netflix", "industry": "Entertainment", "location": "Los Gatos, CA"},
        {"name": "Stripe", "industry": "Fintech", "location": "San Francisco, CA"},
        {"name": "Databricks", "industry": "Data Platform", "location": "San Francisco, CA"},
    ]

    created_companies = []
    for comp in companies:
        created = company_svc.create(**comp)
        created_companies.append(created)
        print(f"  ✓ {created.name}")

    # Positions
    print("\n💼 Creating positions...")
    positions = [
        {"title": "Software Engineer", "level": "Senior"},
        {"title": "Software Engineer", "level": "Mid"},
        {"title": "Backend Engineer", "level": "Senior"},
        {"title": "Frontend Engineer", "level": "Mid"},
        {"title": "Full Stack Engineer", "level": "Senior"},
        {"title": "Data Engineer", "level": "Senior"},
        {"title": "DevOps Engineer", "level": "Mid"},
        {"title": "Site Reliability Engineer", "level": "Senior"},
        {"title": "Engineering Manager", "level": "Lead"},
        {"title": "Student Intern", "level": "Student"},
    ]

    created_positions = []
    for pos in positions:
        created = position_svc.create(**pos)
        created_positions.append(created)
        print(f"  ✓ {created.title} ({created.level})")

    # Recruiters
    print("\n👤 Creating recruiters...")
    recruiters = [
        {
            "name": "Sarah Johnson",
            "email": "sarah.j@google.com",
            "phone": "650-555-0101",
            "company_id": created_companies[0].id,  # Google
        },
        {
            "name": "Mike Chen",
            "email": "mchen@microsoft.com",
            "phone": "425-555-0102",
            "company_id": created_companies[1].id,  # Microsoft
        },
        {
            "name": "Emily Rodriguez",
            "email": "erodriguez@amazon.com",
            "company_id": created_companies[2].id,  # Amazon
        },
    ]

    created_recruiters = []
    for rec in recruiters:
        created = recruiter_svc.create(**rec)
        created_recruiters.append(created)
        print(f"  ✓ {created.name} ({created.email})")

    # Applications with different statuses
    print("\n📝 Creating applications...")

    # Application 1: Google - Interview Scheduled
    app1 = app_svc.create(
        company_id=created_companies[0].id,
        position_id=created_positions[0].id,
        recruiter_id=created_recruiters[0].id,
        applied_date=date.today() - timedelta(days=14),
        notes="Referral from former colleague. Strong team fit."
    )
    app_svc.update_status(app1.id, status_id("Interview Scheduled"))
    event_svc.log(
        app1.id,
        "Interview Scheduled",
        datetime.now() - timedelta(days=2),
        "First round: Technical phone screen scheduled for next Tuesday"
    )
    print(f"  ✓ Application #{app1.id}: Google - Interview Scheduled")

    # Application 2: Microsoft - Interviewed (waiting for offer)
    app2 = app_svc.create(
        company_id=created_companies[1].id,
        position_id=created_positions[2].id,
        recruiter_id=created_recruiters[1].id,
        applied_date=date.today() - timedelta(days=21),
        notes="Applied via LinkedIn. Competitive compensation package."
    )
    app_svc.update_status(app2.id, status_id("Interview Scheduled"))
    app_svc.update_status(app2.id, status_id("Interviewed"))
    event_svc.log(
        app2.id,
        "Interview",
        datetime.now() - timedelta(days=3),
        "Final round onsite - met with 5 engineers and hiring manager"
    )
    print(f"  ✓ Application #{app2.id}: Microsoft - Interviewed")

    # Application 3: Amazon - Offer!
    app3 = app_svc.create(
        company_id=created_companies[2].id,
        position_id=created_positions[5].id,
        recruiter_id=created_recruiters[2].id,
        applied_date=date.today() - timedelta(days=35),
        notes="Dream role - data engineering with distributed systems focus"
    )
    app_svc.update_status(app3.id, status_id("Interview Scheduled"))
    app_svc.update_status(app3.id, status_id("Interviewed"))
    app_svc.update_status(app3.id, status_id("Offer"))
    event_svc.log(
        app3.id,
        "Offer Received",
        datetime.now() - timedelta(days=1),
        "Base: $180k, RSU: $200k over 4 years. Decision deadline in 7 days."
    )
    print(f"  ✓ Application #{app3.id}: Amazon - Offer Received!")

    # Application 4: Meta - Recently Applied
    app4 = app_svc.create(
        company_id=created_companies[3].id,
        position_id=created_positions[4].id,
        applied_date=date.today() - timedelta(days=5),
        notes="Cold application. Strong project match with their AR/VR team."
    )
    print(f"  ✓ Application #{app4.id}: Meta - Applied")

    # Application 5: Stripe - Rejected after interview
    app5 = app_svc.create(
        company_id=created_companies[6].id,
        position_id=created_positions[0].id,
        applied_date=date.today() - timedelta(days=42),
        notes="Payment infrastructure team"
    )
    app_svc.update_status(app5.id, status_id("Interview Scheduled"))
    app_svc.update_status(app5.id, status_id("Interviewed"))
    app_svc.update_status(app5.id, status_id("Rejected"))
    event_svc.log(
        app5.id,
        "Rejection",
        datetime.now() - timedelta(days=7),
        "Moved forward with another candidate. Positive feedback, encouraged to reapply in 6 months."
    )
    print(f"  ✓ Application #{app5.id}: Stripe - Rejected")

    # Application 6: Apple - Applied recently
    app6 = app_svc.create(
        company_id=created_companies[4].id,
        position_id=created_positions[9].id,
        applied_date=date.today() - timedelta(days=2),
        notes="Staff level role - high compensation, but relocation required"
    )
    print(f"  ✓ Application #{app6.id}: Apple - Applied")

    # Application 7: Netflix - Withdrawn
    app7 = app_svc.create(
        company_id=created_companies[5].id,
        position_id=created_positions[3].id,
        applied_date=date.today() - timedelta(days=28),
        notes="Culture concerns after research"
    )
    app_svc.update_status(app7.id, status_id("Withdrawn"))
    event_svc.log(
        app7.id,
        "Withdrawal",
        datetime.now() - timedelta(days=12),
        "Withdrew after learning more about on-call expectations. Not a good fit for work-life balance."
    )
    print(f"  ✓ Application #{app7.id}: Netflix - Withdrawn")

    # Application 8: Databricks - Interview Scheduled
    app8 = app_svc.create(
        company_id=created_companies[7].id,
        position_id=created_positions[5].id,
        applied_date=date.today() - timedelta(days=18),
        notes="Exciting opportunity in data infrastructure"
    )
    app_svc.update_status(app8.id, status_id("Interview Scheduled"))
    event_svc.log(
        app8.id,
        "Interview Scheduled",
        datetime.now() - timedelta(days=1),
        "Recruiter screen next week, followed by technical rounds"
    )
    print(f"  ✓ Application #{app8.id}: Databricks - Interview Scheduled")

    print("\n" + "=" * 60)
    print("✅ Database seeded successfully!")
    print("=" * 60)
    print("\nSummary:")
    print(f"  • {len(created_companies)} companies")
    print(f"  • {len(created_positions)} position types")
    print(f"  • {len(created_recruiters)} recruiters")
    print(f"  • 8 applications with varying statuses")
    print("\nTry these commands:")
    print("  python -m job_tracker.cli menu")
    print("  python -m job_tracker.cli analytics")
    print("  python -m job_tracker.cli list-applications")


if __name__ == "__main__":
    try:
        seed_data()
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

