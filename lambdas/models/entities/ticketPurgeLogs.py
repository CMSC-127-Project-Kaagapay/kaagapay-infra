from sqlalchemy import Integer, String, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
from datetime import datetime
import uuid


class TicketPurgeLogEntity(Base):
    """Proof that a soft-deleted ticket was permanently removed. Deliberately holds no report content."""
    __tablename__ = "ticket_purge_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    public_case_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)  # no foreign key: the admin may be removed later
    purged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False)
