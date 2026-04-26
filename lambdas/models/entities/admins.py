from sqlalchemy import String, text
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
    reviewed_applications = relationship(
        "VolunteerApplicationEntity", back_populates="reviewer"
    )
