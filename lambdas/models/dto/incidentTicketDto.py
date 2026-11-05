from pydantic import BaseModel, Field
import uuid
from typing import Optional
from datetime import datetime

class IncidentTicketCreateDto(BaseModel):
    demographic: str
    locality: str
    involved_party: str
    routing_type: str # "specific" or "random"
    selected_volunteer_id: Optional[uuid.UUID] = None

class IncidentTicketResponseDto(BaseModel):
    id: uuid.UUID
    public_case_id: str
    demographic: str
    locality: str
    involved_party: str
    routing_type: str
    status: str
    assigned_volunteer_id: Optional[uuid.UUID] = None
    assigned_volunteer_handle: Optional[str] = None
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True

class TicketDeleteDto(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=255)

class DeletedTicketResponseDto(IncidentTicketResponseDto):
    deleted_at: datetime
    deleted_by: Optional[uuid.UUID] = None
    deleted_reason: Optional[str] = None

class TicketStatusUpdateDto(BaseModel):
    status: str  # "in_progress", "resolved", "closed"

class TicketStatusLogResponseDto(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    volunteer_id: Optional[uuid.UUID] = None
    from_status: str
    to_status: str

    class Config:
        from_attributes = True