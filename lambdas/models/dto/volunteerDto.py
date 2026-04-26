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
    status: str
    incentive_points: int

    class Config:
        from_attributes = True # Allow ORM models to be used with Pydantic

class VolunteerApplicationCreateDto(BaseModel):
    first_name: str
    last_name: str
    motivation: str
    public_alias: str
    email: str

class VolunteerApplicationResponseDto(BaseModel):
    application_id: uuid.UUID
    first_name: str
    last_name: str
    motivation: str
    public_alias: str
    email: str
    status: str

    class Config:
        from_attributes = True # Allow ORM models to be used with Pydantic