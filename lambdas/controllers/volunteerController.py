from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from repositories.volunteersRepository import VolunteerRepository
from repositories.volunteerApplicationRepository import VolunteerApplicationRepository
from usecases.volunteersUsecase import VolunteersUsecase
from db import get_db
from models.dto.volunteerDto import (
    VolunteerResponseDto,
    VolunteerApplicationCreateDto,
    VolunteerApplicationResponseDto,
)
import uuid
from typing import List

volunteersRouter = APIRouter()


@volunteersRouter.get("/volunteers", response_model=List[VolunteerResponseDto])
async def getVolunteers(db: Session = Depends(get_db)):
    volunteerRepository = VolunteerRepository(db)
    volunteerApplicationRepository = VolunteerApplicationRepository(
        db
    )  # Initialize appRepo
    volunteerUsecase = VolunteersUsecase(
        volunteerRepository, volunteerApplicationRepository
    )
    return volunteerUsecase.getAllVolunteers()


@volunteersRouter.post(
    "/volunteers/from-application/{application_id}",
    response_model=VolunteerResponseDto,
    status_code=status.HTTP_201_CREATED,
)
async def createVolunteerFromApplicationRoute(
    application_id: uuid.UUID, db: Session = Depends(get_db)
):
    volunteerRepository = VolunteerRepository(db)
    volunteerApplicationRepository = VolunteerApplicationRepository(db)
    volunteerUsecase = VolunteersUsecase(
        volunteerRepository, volunteerApplicationRepository
    )
    return volunteerUsecase.createVolunteerFromApplication(application_id)


@volunteersRouter.post(
    "/volunteer-applications",
    response_model=VolunteerApplicationResponseDto,
    status_code=status.HTTP_201_CREATED,
)
async def createVolunteerApplicationRoute(
    app_dto: VolunteerApplicationCreateDto, db: Session = Depends(get_db)
):
    volunteerRepository = VolunteerRepository(db)
    volunteerApplicationRepository = VolunteerApplicationRepository(db)
    volunteerUsecase = VolunteersUsecase(
        volunteerRepository, volunteerApplicationRepository
    )
    return volunteerUsecase.createVolunteerApplication(app_dto)


@volunteersRouter.put(
    "/volunteer-applications/{application_id}/approve",
    response_model=VolunteerApplicationResponseDto,
    status_code=status.HTTP_200_OK,
)
async def approveVolunteerApplicationRoute(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    volunteerRepository = VolunteerRepository(db)
    volunteerApplicationRepository = VolunteerApplicationRepository(db)
    volunteerUsecase = VolunteersUsecase(
        volunteerRepository, volunteerApplicationRepository
    )
    # Pass the obtained admin_id to the usecase
    return volunteerUsecase.approveVolunteerApplication(application_id)
