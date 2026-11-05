from datetime import datetime, timedelta, timezone
import os
import sys

# Add the lambdas directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db import get_db
from repositories.incidentTicketRepository import IncidentTicketRepository
from utils.retention import retention_days

BATCH_SIZE = 200
MAX_BATCHES_PER_RUN = 10  # keeps one run short; the next run carries on


def run_purge_deleted_tickets_worker(now: datetime | None = None, db=None) -> int:
    """Permanently remove tickets that were soft-deleted longer ago than the retention period."""
    days = retention_days()
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=days)
    owns_session = db is None
    db = db or next(get_db())
    removed = 0
    try:
        repo = IncidentTicketRepository(db)
        for _ in range(MAX_BATCHES_PER_RUN):
            batch = repo.purgeDeletedBefore(cutoff, days, BATCH_SIZE)
            removed += batch
            if batch < BATCH_SIZE:
                break
        if removed:
            print(f"Purged {removed} ticket(s) deleted more than {days} days ago.")
        return removed
    except Exception as e:
        print(f"Error in purge worker: {e}")
        return removed
    finally:
        if owns_session:
            db.close()


if __name__ == "__main__":
    run_purge_deleted_tickets_worker()
