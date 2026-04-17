from sqlalchemy import ForeignKey, String, Integer, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import uuid


class VolunteerEntity(Base):
    __tablename__ = "volunteers"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Internal data
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Public-facing data
    public_alias: Mapped[str] = mapped_column(String(50), nullable=False)
    external_handle: Mapped[str] = mapped_column(String(100), nullable=False)

    # State and Gamification
    status: Mapped[str] = mapped_column(String(20), default="active")
    incentive_points: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    claimed_tickets = relationship(
        "IncidentTicketEntity", back_populates="assigned_volunteer"
    )
