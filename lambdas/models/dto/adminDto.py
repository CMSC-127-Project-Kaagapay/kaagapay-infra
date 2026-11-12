from pydantic import BaseModel
import uuid
from typing import Optional
from datetime import datetime


class AdminCreateDto(BaseModel):
    id: uuid.UUID          # the Supabase account (auth user id) to make an admin
    first_name: str
    last_name: str
    email: str
    username: Optional[str] = None
    role: Optional[str] = "admin"
    office_id: Optional[uuid.UUID] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "00000000-0000-0000-0000-000000000000",
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
