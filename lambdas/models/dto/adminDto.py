from pydantic import BaseModel
import uuid
from typing import Optional
from datetime import datetime


class AdminCreateDto(BaseModel):
    first_name: str
    last_name: str
    email: str
    username: Optional[str] = None
    role: Optional[str] = "admin"
    office_id: Optional[uuid.UUID] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "first_name": "Adriane",
                "last_name": "Pena",
                "email": "adrianenathanielpena@gmail.com",
                "username": "yanyan1616",
                "role": "admin",
                "office_id": None
            }
        }
    }




class AdminResponseDto(BaseModel):

    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    username: Optional[str] = None
    role: str
    office_id: Optional[uuid.UUID] = None


    class Config:
        from_attributes = True


class NotificationResponseDto(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    recipient_type: str
    recipient_id: str
    message: str
    status: str
    channel: str
    sent_at: datetime

    class Config:
        from_attributes = True


class AdminMeDto(BaseModel):
    """Who the signed-in admin is. The site uses this to decide whether to show admin pages."""
    id: uuid.UUID
    first_name: str
    last_name: str
    role: Optional[str] = None

    model_config = {"from_attributes": True}


class MonthlyTrendItem(BaseModel):
    label: str
    year: int
    month: int
    count: int


class QuarterlyTrendItem(BaseModel):
    label: str
    year: int
    quarter: int
    count: int


class IncidentTrendsDto(BaseModel):
    monthly: list[MonthlyTrendItem]
    quarterly: list[QuarterlyTrendItem]


class AdminStatsDto(BaseModel):
    active_reports: int
    pending_reports: int
    claimed_reports: int
    in_progress_reports: int
    total_tickets: int
    resolved_tickets: int
    resolution_rate: float
    pending_applications: int
    active_volunteers: int
    incident_trends: IncidentTrendsDto
