"""Tests for volunteer assigned tickets listing and status progression."""
from datetime import datetime, timedelta, timezone
import os
import sys
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.test_ticket_soft_delete import db  # noqa: F401
from models.entities.incidentTickets import IncidentTicketEntity
from models.entities.volunteers import VolunteerEntity
from repositories.adminRepository import AdminRepository
from repositories.incidentTicketRepository import IncidentTicketRepository
from repositories.notificationRepository import NotificationRepository
from repositories.ticketStatusLogRepository import TicketStatusLogRepository
from repositories.volunteersRepository import VolunteerRepository
from usecases.incidentTicketUsecase import IncidentTicketUsecase


def _make_volunteer_client(db, volunteer_id):
    from controllers.incidentTicketController import get_incident_ticket_usecase, router
    from utils.auth import get_current_user_id

    usecase = IncidentTicketUsecase(
        IncidentTicketRepository(db),
        VolunteerRepository(db),
        AdminRepository(db),
        NotificationRepository(db),
        TicketStatusLogRepository(db),
    )

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user_id] = lambda: volunteer_id
    app.dependency_overrides[get_incident_ticket_usecase] = lambda: usecase
    return TestClient(app)


def _seed_volunteer(db):
    vol = VolunteerEntity(
        id=uuid.uuid4(),
        first_name="Alex",
        last_name="Rivera",
        email=f"{uuid.uuid4().hex[:8]}@up.edu.ph",
        public_alias="Responder Alex",
        external_handle="@alex",
        status="active",
    )
    db.add(vol)
    db.commit()
    db.refresh(vol)
    return vol


def _seed_ticket(db, case_id, status="claimed", volunteer_id=None):
    now = datetime.now(timezone.utc)
    ticket = IncidentTicketEntity(
        id=uuid.uuid4(),
        public_case_id=case_id,
        demographic="Undergraduate",
        locality="CHSS",
        involved_party="Peer",
        routing_type="random",
        status=status,
        assigned_volunteer_id=volunteer_id,
        created_at=now,
        expires_at=now + timedelta(minutes=15),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def test_volunteer_assigned_tickets_and_resolve_flow(db):
    vol = _seed_volunteer(db)
    other_vol = _seed_volunteer(db)

    claimed = _seed_ticket(db, "KGP-1001", status="claimed", volunteer_id=vol.id)
    _seed_ticket(db, "KGP-1002", status="requested", volunteer_id=vol.id)
    _seed_ticket(db, "KGP-1003", status="claimed", volunteer_id=other_vol.id)

    client = _make_volunteer_client(db, vol.id)

    # Assigned endpoint returns only claimed/in_progress/resolved/closed for this volunteer
    res = client.get("/incidents/assigned")
    assert res.status_code == 200
    assert [t["public_case_id"] for t in res.json()] == [claimed.public_case_id]

    # Walk through valid transitions: claimed -> in_progress -> resolved -> closed
    for next_status in ("in_progress", "resolved", "closed"):
        patch_res = client.patch(
            f"/incidents/{claimed.public_case_id}/status",
            json={"status": next_status},
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == next_status
