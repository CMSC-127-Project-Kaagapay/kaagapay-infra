from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import uuid

class AlliedOfficeEntity(Base):
    __tablename__ = "allied_offices"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    acronym: Mapped[str] = mapped_column(String(50), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    volunteers = relationship("VolunteerEntity", back_populates="office")
    admins = relationship("AdminEntity", back_populates="office")
    contact_lines = relationship("ContactLineEntity", back_populates="office")