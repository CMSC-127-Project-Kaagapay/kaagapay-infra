from pydantic import BaseModel
import uuid
from typing import Optional

class AlliedOfficeResponseDto(BaseModel):
    id: uuid.UUID
    name: str
    contact_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

    class Config:
        from_attributes = True
