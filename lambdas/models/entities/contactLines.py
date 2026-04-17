from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import uuid

class ContactLineEntity(Base):
    __tablename__ = "contact_lines"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    office_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("allied_offices.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    office = relationship("AlliedOfficeEntity", back_populates="contact_lines")