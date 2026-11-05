"""Plain error messages (no internals leaked) and readable, unguessable, collision-safe Case IDs."""
import logging
import os
import sys
import uuid
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.test_ticket_soft_delete import db, admin  # noqa: F401  (fixtures)
from models.dto.incidentTicketDto import IncidentTicketCreateDto
from models.entities.admins import AdminEntity  # noqa: F401
from models.entities.incidentTickets import IncidentTicketEntity
from repositories.adminRepository import AdminRepository
from repositories.incidentTicketRepository import IncidentTicketRepository
from repositories.notificationRepository import NotificationRepository
from repositories.ticketStatusLogRepository import TicketStatusLogRepository
from repositories.volunteersRepository import VolunteerRepository
from usecases.incidentTicketUsecase import IncidentTicketUsecase
from utils import case_id as case_id_module
from utils.case_id import ALPHABET, CASE_ID_PATTERN, generate_case_id
from utils.errors import GENERIC_MESSAGE, internal_error

SECRET = "password authentication failed for user postgres at db.secret-host.supabase.co:5432"


# ---- Case IDs ---------------------------------------------------------------------------------------

def test_case_ids_never_use_look_alike_characters():
    for ch in "O0I1L":
        assert ch not in ALPHABET
    ids = [generate_case_id() for _ in range(3000)]
    assert all(CASE_ID_PATTERN.match(i) for i in ids)
    assert not any(c in i[5:] for i in ids for c in "O0I1L-" if c != "-")


def test_case_ids_are_spread_over_the_whole_alphabet_and_do_not_repeat():
    ids = [generate_case_id() for _ in range(3000)]
    assert len(set(ids)) == len(ids)
    used = {c for i in ids for c in i.replace("KGPY-", "").replace("-", "")}
    assert used == set(ALPHABET)


def test_case_ids_come_from_the_secure_random_source(monkeypatch):
    calls = []
    monkeypatch.setattr(case_id_module.secrets, "choice", lambda seq: calls.append(1) or seq[0])
    assert generate_case_id() == "KGPY-AAAA-AAAA" and len(calls) == 8


@pytest.fixture()
def usecase(db):
    return IncidentTicketUsecase(IncidentTicketRepository(db), VolunteerRepository(db), AdminRepository(db), NotificationRepository(db), TicketStatusLogRepository(db))


def report(**kw):
    return IncidentTicketCreateDto(demographic="Harassment", locality="Campus", involved_party="Student", routing_type=kw.pop("routing_type", "random"), **kw)


def test_a_new_report_gets_a_readable_case_id(usecase):
    assert CASE_ID_PATTERN.match(usecase.createIncidentReport(report()).public_case_id)


def test_a_clash_on_the_case_id_is_retried_instead_of_failing(db, usecase, monkeypatch):
    now = datetime.now(timezone.utc)
    db.add(IncidentTicketEntity(id=uuid.uuid4(), public_case_id="KGPY-AAAA-AAAA", demographic="x", locality="x", involved_party="x", routing_type="random", status="pending", created_at=now, expires_at=now))
    db.commit()
    ids = iter(["KGPY-AAAA-AAAA", "KGPY-AAAA-AAAA", "KGPY-BBBB-CCCC"])
    monkeypatch.setattr("usecases.incidentTicketUsecase.generate_case_id", lambda: next(ids))
    assert usecase.createIncidentReport(report()).public_case_id == "KGPY-BBBB-CCCC"


def test_a_specific_report_without_a_volunteer_is_a_400_not_a_crash(usecase):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        usecase.createIncidentReport(report(routing_type="specific"))
    assert exc.value.status_code == 400


# ---- plain error messages ----------------------------------------------------------------------------

def test_internal_error_hides_the_cause_and_logs_it(caplog):
    with caplog.at_level(logging.ERROR, logger="kaagapay"):
        error = internal_error(RuntimeError(SECRET), "report")
    assert error.status_code == 500
    assert error.detail.startswith(GENERIC_MESSAGE) and "Reference:" in error.detail
    assert "secret-host" not in error.detail and "password" not in error.detail
    reference = error.detail.split("Reference: ")[1].rstrip(")")
    assert SECRET in caplog.text and reference in caplog.text      # the operator can find it by the reference


def test_a_failing_report_endpoint_does_not_leak_the_cause(db):
    from controllers.incidentTicketController import router, get_incident_ticket_usecase

    class Broken:
        def createIncidentReport(self, dto):
            raise RuntimeError(SECRET)

    app = FastAPI(); app.include_router(router); app.dependency_overrides[get_incident_ticket_usecase] = lambda: Broken()
    r = TestClient(app).post("/incidents", json={"demographic": "a", "locality": "b", "involved_party": "c", "routing_type": "random"})
    assert r.status_code == 500 and "secret-host" not in r.text and "password" not in r.text and GENERIC_MESSAGE in r.json()["detail"]


def test_an_error_nobody_caught_gets_the_same_plain_message():
    from main import app
    from db import get_db

    def boom():
        raise RuntimeError(SECRET)

    app.dependency_overrides[get_db] = boom
    try:
        r = TestClient(app, raise_server_exceptions=False).get("/volunteers")
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert r.status_code == 500 and "secret-host" not in r.text and GENERIC_MESSAGE in r.json()["detail"]
