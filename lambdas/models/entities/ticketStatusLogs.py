from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import uuid

class TicketStatusLogEntity(Base):
    __tablename__ = "ticket_status_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("incident_tickets.id"), nullable=False)
    volunteer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("volunteers.id"), nullable=True)
    from_status: Mapped[str] = mapped_column(String(100), nullable=False)
    to_status: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    ticket = relationship("IncidentTicketEntity", back_populates="status_logs")
    volunteer = relationship("VolunteerEntity", back_populates="status_logs")
