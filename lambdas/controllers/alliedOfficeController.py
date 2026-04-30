from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
from typing import List

from db import get_db
from models.dto.alliedOfficeDto import AlliedOfficeResponseDto
from repositories.alliedOfficeRepository import AlliedOfficeRepository

router = APIRouter()

@router.get("/offices", response_model=List[AlliedOfficeResponseDto])
async def get_all_offices(db: Session = Depends(get_db)):
    """
    Information Hub: Retrieves all allied offices and their contact info.
    """
    repo = AlliedOfficeRepository(db)
    offices = repo.getAllOffices()
    return [AlliedOfficeResponseDto.model_validate(o) for o in offices]

@router.get("/offices/{office_id}", response_model=AlliedOfficeResponseDto)
async def get_office_details(office_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves details for a specific allied office.
    """
    repo = AlliedOfficeRepository(db)
    office = repo.getOfficeById(office_id)
    if not office:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Office with ID {office_id} not found."
        )
    return AlliedOfficeResponseDto.model_validate(office)
