"""Filters and pagination for the admin ticket list, against in-memory SQLite."""
import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.test_ticket_soft_delete import db, admin, usecase, make_ticket  # noqa: F401  (fixtures)
from models.entities.volunteers import VolunteerEntity
from models.entities.incidentTickets import IncidentTicketEntity
from repositories.incidentTicketRepository import IncidentTicketRepository


def make_volunteer(db, handle):
    v = VolunteerEntity(
        id=uuid.uuid4(), first_name="V", last_name=handle, email=f"{handle}@x.y",
        public_alias=handle, external_handle=handle, status="active", incentive_points=0,
    )
    db.add(v)
    db.commit()
    return v


def make_at(db, case_id, created, status="pending", volunteer=None):
    t = IncidentTicketEntity(
        id=uuid.uuid4(), public_case_id=case_id, demographic="d", locality="l", involved_party="p",
        routing_type="random", status=status, created_at=created,
        expires_at=created + timedelta(minutes=15),
        assigned_volunteer_id=volunteer.id if volunteer else None,
    )
    db.add(t)
    db.commit()
    return t


def ids(items):
    return [t.public_case_id for t in items]


def test_pages_are_stable_and_total_matches(db):
    base = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    for i in range(7):
        # Same timestamp for all: the id tiebreaker has to keep pages from overlapping.
        make_at(db, f"KGPY-P-{i:04d}", base)
    repo = IncidentTicketRepository(db)
    p1, total = repo.getTicketsPage("pending", None, None, None, 1, 3)
    p2, _ = repo.getTicketsPage("pending", None, None, None, 2, 3)
    p3, _ = repo.getTicketsPage("pending", None, None, None, 3, 3)
    assert total == 7
    assert len(p1) == 3 and len(p2) == 3 and len(p3) == 1
    assert len(set(ids(p1) + ids(p2) + ids(p3))) == 7


def test_page_past_the_end_is_empty_but_total_is_kept(db):
    make_at(db, "KGPY-E-0001", datetime(2026, 10, 1, tzinfo=timezone.utc))
    items, total = IncidentTicketRepository(db).getTicketsPage("pending", None, None, None, 5, 25)
    assert items == [] and total == 1


def test_filter_by_volunteer(db):
    a, b = make_volunteer(db, "ana"), make_volunteer(db, "ben")
    when = datetime(2026, 10, 1, tzinfo=timezone.utc)
    make_at(db, "KGPY-V-0001", when, status="claimed", volunteer=a)
    make_at(db, "KGPY-V-0002", when, status="claimed", volunteer=b)
    items, total = IncidentTicketRepository(db).getTicketsPage("claimed", a.id, None, None, 1, 25)
    assert ids(items) == ["KGPY-V-0001"] and total == 1


def test_date_range_is_inclusive_on_both_ends(db):
    make_at(db, "KGPY-D-0001", datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc))
    make_at(db, "KGPY-D-0002", datetime(2026, 10, 3, 23, 59, tzinfo=timezone.utc))
    make_at(db, "KGPY-D-0003", datetime(2026, 10, 4, 0, 0, tzinfo=timezone.utc))
    make_at(db, "KGPY-D-0004", datetime(2026, 9, 30, 23, 59, tzinfo=timezone.utc))
    items, total = IncidentTicketRepository(db).getTicketsPage(
        "pending", None, date(2026, 10, 1), date(2026, 10, 3), 1, 25
    )
    assert sorted(ids(items)) == ["KGPY-D-0001", "KGPY-D-0002"] and total == 2


def test_filters_combine_with_status_and_exclude_deleted(db, usecase, admin):
    v = make_volunteer(db, "cy")
    when = datetime(2026, 10, 2, tzinfo=timezone.utc)
    make_at(db, "KGPY-C-0001", when, status="claimed", volunteer=v)
    gone = make_at(db, "KGPY-C-0002", when, status="claimed", volunteer=v)
    make_at(db, "KGPY-C-0003", when, status="resolved", volunteer=v)
    usecase.deleteTicket(gone.public_case_id, admin.id, None)
    items, total = IncidentTicketRepository(db).getTicketsPage("claimed", v.id, date(2026, 10, 2), None, 1, 25)
    assert ids(items) == ["KGPY-C-0001"] and total == 1


@pytest.fixture()
def client(db, admin):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from controllers.adminController import router
    from db import get_db
    from utils.auth import get_current_admin

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_admin] = lambda: admin.id
    return TestClient(app)


def test_endpoint_returns_page_envelope(client, db):
    base = datetime(2026, 10, 1, tzinfo=timezone.utc)
    for i in range(3):
        make_at(db, f"KGPY-A-{i:04d}", base + timedelta(minutes=i))
    r = client.get("/admin/tickets/pending", params={"page": 2, "page_size": 2})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3 and body["page"] == 2 and body["page_size"] == 2
    assert [t["public_case_id"] for t in body["items"]] == ["KGPY-A-0000"]


def test_endpoint_rejects_bad_input(client):
    assert client.get("/admin/tickets/pending", params={"page": 0}).status_code == 422
    assert client.get("/admin/tickets/pending", params={"page_size": 101}).status_code == 422
    assert client.get("/admin/tickets/bogus").status_code == 422
    r = client.get("/admin/tickets/pending", params={"date_from": "2026-10-05", "date_to": "2026-10-01"})
    assert r.status_code == 422


def test_deleted_route_is_not_shadowed_by_status_route(client):
    assert client.get("/admin/tickets/deleted").status_code == 200
