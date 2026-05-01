from sqlalchemy import ForeignKey, String, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import uuid
from datetime import datetime

class NotificationEntity(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("incident_tickets.id"), nullable=False)
    recipient_type: Mapped[str] = mapped_column(String(100), nullable=False)  # Volunteer or Admin
    recipient_id: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="unread")
    channel: Mapped[str] = mapped_column(String(100), nullable=False, default="dashboard")  # Push, Email, Dashboard
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    # Relationships
    ticket = relationship("IncidentTicketEntity", back_populates="notifications")