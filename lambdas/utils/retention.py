import os

DEFAULT_RETENTION_DAYS = 30
MAX_RETENTION_DAYS = 3650


def retention_days() -> int:
    """How long a soft-deleted ticket can be restored before it is permanently removed (TICKET_RETENTION_DAYS)."""
    raw = os.getenv("TICKET_RETENTION_DAYS", "")
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_RETENTION_DAYS
    return value if 1 <= value <= MAX_RETENTION_DAYS else DEFAULT_RETENTION_DAYS
