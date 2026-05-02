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
    VolunteerUpdateDto,
)
import uuid
from typing import List, Dict
from utils.auth import get_current_admin, get_current_user_id

volunteersRouter = APIRouter()


@volunteersRouter.get(
    "/volunteers/profile-image-upload-url", response_model=Dict[str, str]
)
async def getProfileImageUploadUrlRoute(db: Session = Depends(get_db)):
    volunteerRepository = VolunteerRepository(db)
    volunteerApplicationRepository = VolunteerApplicationRepository(db)
    volunteerUsecase = VolunteersUsecase(
        volunteerRepository, volunteerApplicationRepository
    )
    return volunteerUsecase.getProfileImageUploadUrl()


@volunteersRouter.patch(
    "/volunteers/{volunteer_id}", response_model=VolunteerResponseDto
)
async def updateVolunteerRoute(
    volunteer_id: uuid.UUID,
    update_dto: VolunteerUpdateDto,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(
        get_current_user_id
    ),  # Using general auth to allow volunteers to update themselves
):
    # Depending on auth requirements, we might want to check if current_user_id == volunteer_id
    volunteerRepository = VolunteerRepository(db)
    volunteerApplicationRepository = VolunteerApplicationRepository(db)
    volunteerUsecase = VolunteersUsecase(
        volunteerRepository, volunteerApplicationRepository
    )
    return volunteerUsecase.updateVolunteer(volunteer_id, update_dto)


@volunteersRouter.get("/volunteers/{volunteer_id}", response_model=VolunteerResponseDto)
async def getVolunteer(volunteer_id: uuid.UUID, db: Session = Depends(get_db)):
    volunteerRepository = VolunteerRepository(db)
    volunteerApplicationRepository = VolunteerApplicationRepository(db)
    volunteerUsecase = VolunteersUsecase(
        volunteerRepository, volunteerApplicationRepository
    )
    return volunteerUsecase.getVolunteerById(volunteer_id)


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

@volunteersRouter.get(
    "/volunteer-applications",
    response_model=List[VolunteerApplicationResponseDto],
    status_code=status.HTTP_200_OK,
)
async def getVolunteerApplicationRoute(db: Session = Depends(get_db)):
    volunteerRepository = VolunteerRepository(db)
    volunteerApplicationRepository = VolunteerApplicationRepository(db)
    volunteerUsecase = VolunteersUsecase(
        volunteerRepository, volunteerApplicationRepository
    )
    return volunteerUsecase.getAllVolunteerApplications()



@volunteersRouter.put(
    "/volunteer-applications/{application_id}/approve",
    response_model=VolunteerApplicationResponseDto,
    status_code=status.HTTP_200_OK,
)
async def approveVolunteerApplicationRoute(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin),
):
    volunteerRepository = VolunteerRepository(db)
    volunteerApplicationRepository = VolunteerApplicationRepository(db)
    volunteerUsecase = VolunteersUsecase(
        volunteerRepository, volunteerApplicationRepository
    )
    # Pass the obtained admin_id to the usecase
    return volunteerUsecase.approveVolunteerApplication(application_id, admin_id)


@volunteersRouter.put(
    "/volunteer-applications/{application_id}/reject",
    response_model=VolunteerApplicationResponseDto,
    status_code=status.HTTP_200_OK,
)
async def rejectVolunteerApplicationRoute(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin),
):
    volunteerRepository = VolunteerRepository(db)
    volunteerApplicationRepository = VolunteerApplicationRepository(db)
    volunteerUsecase = VolunteersUsecase(
        volunteerRepository, volunteerApplicationRepository
    )
    # Pass the obtained admin_id to the usecase
    return volunteerUsecase.rejectVolunteerApplication(application_id, admin_id)
