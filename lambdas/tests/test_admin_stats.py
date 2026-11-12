"""GET /admin/stats: Real summary metrics and incident trends."""
import os
import sys
import uuid
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.test_ticket_soft_delete import db, admin, make_ticket  # noqa: F401  (fixtures)
from models.entities.volunteerApplications import VolunteerApplicationEntity
from models.entities.volunteers import VolunteerEntity


def make_client(db, user_id, is_admin):
    from controllers.adminController import router
    from db import get_db
    from utils.auth import get_current_admin

    def current_admin():
        if not is_admin:
            raise HTTPException(status_code=403, detail="Access denied: User is not an admin")
        return user_id

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_admin] = current_admin
    return TestClient(app)


def test_admin_stats_empty(db, admin):
    client = make_client(db, admin.id, True)
    r = client.get("/admin/stats")
    assert r.status_code == 200
    data = r.json()

    assert data["active_reports"] == 0
    assert data["pending_reports"] == 0
    assert data["claimed_reports"] == 0
    assert data["in_progress_reports"] == 0
    assert data["total_tickets"] == 0
    assert data["resolved_tickets"] == 0
    assert data["resolution_rate"] == 0.0
    assert data["pending_applications"] == 0
    assert data["active_volunteers"] == 0
    assert len(data["incident_trends"]["monthly"]) == 6
    assert len(data["incident_trends"]["quarterly"]) == 4
    assert all(item["count"] == 0 for item in data["incident_trends"]["monthly"])
    assert all(item["count"] == 0 for item in data["incident_trends"]["quarterly"])


def test_admin_stats_with_data(db, admin):
    # Tickets
    t1 = make_ticket(db, "CAS-001", status="pending")
    t2 = make_ticket(db, "CAS-002", status="in_progress")
    t3 = make_ticket(db, "CAS-003", status="resolved")
    t4_deleted = make_ticket(db, "CAS-004", status="pending")
    t4_deleted.deleted_at = datetime.now(timezone.utc)
    db.commit()

    # Volunteer Applications
    va1 = VolunteerApplicationEntity(
        first_name="Jane", last_name="Doe", motivation="Help",
        public_alias="jdoe", external_handle="@jdoe", email="jane@example.com",
        status="pending"
    )
    va2 = VolunteerApplicationEntity(
        first_name="John", last_name="Smith", motivation="Help",
        public_alias="jsmith", external_handle="@jsmith", email="john@example.com",
        status="approved"
    )
    db.add_all([va1, va2])

    # Volunteers
    v1 = VolunteerEntity(
        first_name="Alice", last_name="V", email="alice@example.com",
        public_alias="alice", external_handle="@alice", status="active"
    )
    v2 = VolunteerEntity(
        first_name="Bob", last_name="V", email="bob@example.com",
        public_alias="bob", external_handle="@bob", status="inactive"
    )
    db.add_all([v1, v2])
    db.commit()

    client = make_client(db, admin.id, True)
    r = client.get("/admin/stats")
    assert r.status_code == 200
    data = r.json()

    assert data["active_reports"] == 2  # pending + in_progress (CAS-004 is deleted)
    assert data["pending_reports"] == 1
    assert data["claimed_reports"] == 0
    assert data["in_progress_reports"] == 1
    assert data["total_tickets"] == 3
    assert data["resolved_tickets"] == 1
    assert data["resolution_rate"] == 33.3
    assert data["pending_applications"] == 1
    assert data["active_volunteers"] == 1

    # Current month should have 3 tickets created
    monthly = data["incident_trends"]["monthly"]
    assert len(monthly) == 6
    assert monthly[-1]["count"] == 3


def test_admin_stats_requires_admin(db, admin):
    client = make_client(db, admin.id, False)
    assert client.get("/admin/stats").status_code == 403
