from sqlalchemy import String, text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import uuid


class AdminEntity(Base):
    __tablename__ = "admins"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    
    office_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("allied_offices.id"), nullable=True)
    username: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="admin")

    # Relationships
    office = relationship("AlliedOfficeEntity", back_populates="admins")
    reviewed_applications = relationship(
        "VolunteerApplicationEntity", back_populates="reviewer"
    )
