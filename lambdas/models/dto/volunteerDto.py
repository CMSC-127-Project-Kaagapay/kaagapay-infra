from pydantic import BaseModel
import uuid
from typing import Optional


class VolunteerCreateDto(BaseModel):
    first_name: str
    last_name: str
    email: str
    public_alias: str
    external_handle: str # Assuming this will be derived or set during creation

class VolunteerResponseDto(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    public_alias: str
    external_handle: str
    profile_image_url: Optional[str] = None # This will be the generated URL
    status: str
    incentive_points: int
    office_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True # Allow ORM models to be used with Pydantic

class VolunteerUpdateDto(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    public_alias: Optional[str] = None
    external_handle: Optional[str] = None
    profile_image_key: Optional[str] = None

class VolunteerApplicationCreateDto(BaseModel):
    first_name: str
    last_name: str
    motivation: str
    public_alias: str
    email: str
    external_handle: str

class VolunteerApplicationResponseDto(BaseModel):
    application_id: uuid.UUID
    first_name: str
    last_name: str
    motivation: str
    public_alias: str
    email: str
    status: str
    external_handle: str

    class Config:
        from_attributes = True # Allow ORM models to be used with Pydantic