"""Permanent removal of soft-deleted tickets after the retention period."""
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import inspect

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.test_ticket_soft_delete import db, admin, usecase, make_ticket  # noqa: F401  (fixtures)
from models.entities.incidentTickets import IncidentTicketEntity
from models.entities.notifications import NotificationEntity
from models.entities.ticketStatusLogs import TicketStatusLogEntity
from models.entities.ticketPurgeLogs import TicketPurgeLogEntity
from repositories.incidentTicketRepository import IncidentTicketRepository
from cron_jobs.purge_deleted_tickets_worker import run_purge_deleted_tickets_worker
from utils.retention import retention_days

NOW = datetime(2026, 11, 5, 12, tzinfo=timezone.utc)


def delete_at(db, usecase, admin, ticket, when, reason="test"):
    usecase.deleteTicket(ticket.public_case_id, admin.id, reason)
    db.query(IncidentTicketEntity).filter_by(id=ticket.id).update({"deleted_at": when})
    db.commit()


def add_related(db, ticket):
    db.add(NotificationEntity(id=uuid.uuid4(), ticket_id=ticket.id, recipient_type="Admin", recipient_id="x", message="m", status="sent"))
    db.commit()


def ids(db):
    return {t.public_case_id for t in db.query(IncidentTicketEntity).all()}


def test_default_retention_is_30_days_and_bad_values_fall_back(monkeypatch):
    monkeypatch.delenv("TICKET_RETENTION_DAYS", raising=False)
    assert retention_days() == 30
    for bad in ("abc", "0", "-5", "99999", ""):
        monkeypatch.setenv("TICKET_RETENTION_DAYS", bad)
        assert retention_days() == 30
    monkeypatch.setenv("TICKET_RETENTION_DAYS", "7")
    assert retention_days() == 7


def test_only_tickets_past_the_retention_period_are_removed(db, usecase, admin, monkeypatch):
    monkeypatch.delenv("TICKET_RETENTION_DAYS", raising=False)
    live = make_ticket(db, "KGPY-P-LIVE")
    recent = make_ticket(db, "KGPY-P-RECENT")
    old = make_ticket(db, "KGPY-P-OLD")
    delete_at(db, usecase, admin, recent, NOW - timedelta(days=29))
    delete_at(db, usecase, admin, old, NOW - timedelta(days=31))

    assert run_purge_deleted_tickets_worker(now=NOW, db=db) == 1
    assert ids(db) == {"KGPY-P-LIVE", "KGPY-P-RECENT"}


def test_logs_and_notifications_go_with_the_ticket_and_the_audit_row_has_no_content(db, usecase, admin):
    old = make_ticket(db, "KGPY-P-OLD2")
    add_related(db, old)
    delete_at(db, usecase, admin, old, NOW - timedelta(days=60), reason="duplicate of another report")
    other = make_ticket(db, "KGPY-P-KEEP")
    add_related(db, other)
    old_id = old.id

    run_purge_deleted_tickets_worker(now=NOW, db=db)

    assert db.query(NotificationEntity).filter_by(ticket_id=old_id).count() == 0
    assert db.query(TicketStatusLogEntity).filter_by(ticket_id=old_id).count() == 0
    assert db.query(NotificationEntity).filter_by(ticket_id=other.id).count() == 1   # unrelated rows untouched
    entry = db.query(TicketPurgeLogEntity).one()
    assert (entry.public_case_id, entry.retention_days, entry.deleted_by) == ("KGPY-P-OLD2", 30, admin.id)
    columns = {c.name for c in inspect(TicketPurgeLogEntity).columns}
    assert columns == {"id", "public_case_id", "deleted_at", "deleted_by", "purged_at", "retention_days"}  # no demographic/locality/reason


def test_a_restored_ticket_is_never_purged(db, usecase, admin):
    t = make_ticket(db, "KGPY-P-BACK")
    delete_at(db, usecase, admin, t, NOW - timedelta(days=90))
    usecase.restoreTicket(t.public_case_id)
    assert run_purge_deleted_tickets_worker(now=NOW, db=db) == 0
    assert "KGPY-P-BACK" in ids(db)


def test_running_twice_is_harmless_and_the_retention_setting_is_respected(db, usecase, admin, monkeypatch):
    t = make_ticket(db, "KGPY-P-SHORT")
    delete_at(db, usecase, admin, t, NOW - timedelta(days=10))
    assert run_purge_deleted_tickets_worker(now=NOW, db=db) == 0          # 10 days < 30
    monkeypatch.setenv("TICKET_RETENTION_DAYS", "7")
    assert run_purge_deleted_tickets_worker(now=NOW, db=db) == 1          # 10 days > 7
    assert run_purge_deleted_tickets_worker(now=NOW, db=db) == 0          # nothing left to do
    assert db.query(TicketPurgeLogEntity).count() == 1


def test_large_backlog_is_removed_in_batches(db, usecase, admin, monkeypatch):
    import cron_jobs.purge_deleted_tickets_worker as worker
    monkeypatch.setattr(worker, "BATCH_SIZE", 3)
    for i in range(8):
        delete_at(db, usecase, admin, make_ticket(db, f"KGPY-B-{i:04d}"), NOW - timedelta(days=40 + i))
    assert worker.run_purge_deleted_tickets_worker(now=NOW, db=db) == 8
    assert ids(db) == set()


def test_failure_in_a_batch_removes_nothing_from_that_batch(db, usecase, admin, monkeypatch):
    t = make_ticket(db, "KGPY-P-FAIL")
    delete_at(db, usecase, admin, t, NOW - timedelta(days=60))
    repo = IncidentTicketRepository(db)
    original_commit = db.commit

    def boom():
        raise RuntimeError("database went away")
    monkeypatch.setattr(db, "commit", boom)
    with pytest.raises(RuntimeError):
        repo.purgeDeletedBefore(NOW - timedelta(days=30), 30)
    monkeypatch.setattr(db, "commit", original_commit)
    assert "KGPY-P-FAIL" in ids(db) and db.query(TicketPurgeLogEntity).count() == 0


def test_deleted_list_tells_when_each_ticket_will_be_removed(db, usecase, admin, monkeypatch):
    monkeypatch.delenv("TICKET_RETENTION_DAYS", raising=False)
    t = make_ticket(db, "KGPY-P-DUE")
    result = usecase.deleteTicket(t.public_case_id, admin.id, None)
    assert result.purge_at is not None and timedelta(days=29, hours=23) < (result.purge_at.replace(tzinfo=None) - result.deleted_at.replace(tzinfo=None)) <= timedelta(days=30, minutes=1)
    assert usecase.getDeletedTickets()[0].purge_at == result.purge_at
