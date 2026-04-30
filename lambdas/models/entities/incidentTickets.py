from sqlalchemy import ForeignKey, String, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from datetime import datetime
import uuid

class IncidentTicketEntity(Base):
    __tablename__ = "incident_tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    public_case_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    demographic: Mapped[str] = mapped_column(String(50), nullable=False)
    locality: Mapped[str] = mapped_column(String(50), nullable=False)
    involved_party: Mapped[str] = mapped_column(String(50), nullable=False)
    routing_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Specific or Random
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # Pending, Claimed, Resolved
    assigned_volunteer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("volunteers.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    assigned_volunteer = relationship("VolunteerEntity", back_populates="claimed_tickets")
    status_logs = relationship("TicketStatusLogEntity", back_populates="ticket")
    notifications = relationship("NotificationEntity", back_populates="ticket")
