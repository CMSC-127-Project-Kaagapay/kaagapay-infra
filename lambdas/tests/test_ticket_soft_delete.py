"""Soft delete behaviour for incident tickets, run against in-memory SQLite (no Supabase needed)."""
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.entities.base import Base
from models.entities.volunteers import VolunteerEntity  # noqa: F401  (register mappers)
from models.entities.programs import ProgramEntity  # noqa: F401
from models.entities.volunteerApplications import VolunteerApplicationEntity  # noqa: F401
from models.entities.alliedOffices import AlliedOfficeEntity  # noqa: F401
from models.entities.contactLines import ContactLineEntity  # noqa: F401
from models.entities.notifications import NotificationEntity  # noqa: F401
from models.entities.ticketStatusLogs import TicketStatusLogEntity
from models.entities.incidentTickets import IncidentTicketEntity
from models.entities.admins import AdminEntity
from repositories.incidentTicketRepository import IncidentTicketRepository
from repositories.ticketStatusLogRepository import TicketStatusLogRepository
from usecases.incidentTicketUsecase import IncidentTicketUsecase


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def _add_pg_functions(dbapi_conn, _):
        # Postgres' gen_random_uuid() doesn't exist in SQLite; SQLAlchemy stores UUIDs as 32-char hex there.
        dbapi_conn.create_function("gen_random_uuid", 0, lambda: uuid.uuid4().hex)
        dbapi_conn.create_function("now", 0, lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))

    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def make_ticket(db, case_id, status="pending", created_offset=0):
    now = datetime.now(timezone.utc)
    ticket = IncidentTicketEntity(
        id=uuid.uuid4(), public_case_id=case_id, demographic="student", locality="Davao",
        involved_party="peer", routing_type="random", status=status,
        created_at=now + timedelta(minutes=created_offset), expires_at=now + timedelta(minutes=15),
    )
    db.add(ticket)
    db.commit()
    return ticket


@pytest.fixture()
def admin(db):
    a = AdminEntity(id=uuid.uuid4(), first_name="A", last_name="B", email="a@b.c")
    db.add(a)
    db.commit()
    return a


@pytest.fixture()
def usecase(db):
    return IncidentTicketUsecase(
        IncidentTicketRepository(db), None, None, None, TicketStatusLogRepository(db)
    )


def test_deleted_ticket_disappears_from_every_read(db, usecase, admin):
    keep = make_ticket(db, "KGPY-AAAA-0001")
    gone = make_ticket(db, "KGPY-AAAA-0002")
    repo = IncidentTicketRepository(db)

    usecase.deleteTicket(gone.public_case_id, admin.id, "duplicate report")

    assert repo.getIncidentTicketByPublicId(gone.public_case_id) is None
    assert repo.getIncidentTicketById(gone.id) is None
    assert [t.public_case_id for t in repo.getAllIncidentTickets()] == [keep.public_case_id]
    assert [t.public_case_id for t in repo.getTicketsByStatus("pending")] == [keep.public_case_id]
    assert [t.public_case_id for t in repo.getPendingTicketsNoVolunteers()] == [keep.public_case_id]
    with pytest.raises(HTTPException) as exc:
        usecase.getIncidentTicket(gone.public_case_id)
    assert exc.value.status_code == 404


def test_delete_records_who_why_and_logs_it(db, usecase, admin):
    t = make_ticket(db, "KGPY-AAAA-0003", status="claimed")
    result = usecase.deleteTicket(t.public_case_id, admin.id, "  test data  ")

    assert result.deleted_by == admin.id
    assert result.deleted_reason == "test data"
    assert result.deleted_at is not None
    logs = db.query(TicketStatusLogEntity).filter_by(ticket_id=t.id).all()
    assert [(l.from_status, l.to_status) for l in logs] == [("claimed", "deleted")]
    assert [d.public_case_id for d in usecase.getDeletedTickets()] == [t.public_case_id]


def test_deleting_twice_is_404(db, usecase, admin):
    t = make_ticket(db, "KGPY-AAAA-0004")
    usecase.deleteTicket(t.public_case_id, admin.id, None)
    with pytest.raises(HTTPException) as exc:
        usecase.deleteTicket(t.public_case_id, admin.id, None)
    assert exc.value.status_code == 404


def test_restore_brings_ticket_back_with_original_status(db, usecase, admin):
    t = make_ticket(db, "KGPY-AAAA-0005", status="in_progress")
    usecase.deleteTicket(t.public_case_id, admin.id, "oops")
    restored = usecase.restoreTicket(t.public_case_id)

    assert restored.status == "in_progress"
    repo = IncidentTicketRepository(db)
    assert repo.getIncidentTicketByPublicId(t.public_case_id) is not None
    assert usecase.getDeletedTickets() == []
    logs = db.query(TicketStatusLogEntity).filter_by(ticket_id=t.id).all()
    assert [(l.from_status, l.to_status) for l in logs] == [("in_progress", "deleted"), ("deleted", "in_progress")]


def test_restoring_a_live_ticket_is_404(db, usecase):
    t = make_ticket(db, "KGPY-AAAA-0006")
    with pytest.raises(HTTPException) as exc:
        usecase.restoreTicket(t.public_case_id)
    assert exc.value.status_code == 404


def test_list_order_is_newest_first_with_id_tiebreak(db):
    a = make_ticket(db, "KGPY-AAAA-0007", created_offset=0)
    b = make_ticket(db, "KGPY-AAAA-0008", created_offset=5)
    ids = [t.public_case_id for t in IncidentTicketRepository(db).getTicketsByStatus("pending")]
    assert ids == [b.public_case_id, a.public_case_id]
