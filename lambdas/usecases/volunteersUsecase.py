from fastapi import HTTPException, status
from models.entities.volunteers import VolunteerEntity
from models.entities.volunteerApplications import VolunteerApplicationEntity
from repositories.volunteersRepository import VolunteerRepository
from repositories.volunteerApplicationRepository import VolunteerApplicationRepository
from models.dto.volunteerDto import VolunteerResponseDto, VolunteerApplicationCreateDto, VolunteerApplicationResponseDto
import uuid
from typing import List


class VolunteersUsecase:
    def __init__(self, volsRepo: VolunteerRepository, appRepo: VolunteerApplicationRepository):
        self.volsRepo = volsRepo
        self.appRepo = appRepo

    def getAllVolunteers(self) -> List[VolunteerResponseDto]:
        try:
            volunteers_entities = self.volsRepo.getAllVolunteers()
            return [VolunteerResponseDto.model_validate(v) for v in volunteers_entities]
        except Exception as e:
            raise e

    def createVolunteerFromApplication(self, application_id: uuid.UUID) -> VolunteerResponseDto:
        application = self.appRepo.getVolunteerApplicationById(application_id)

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Volunteer application with id {application_id} not found."
            )

        if application.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Volunteer application {application_id} is not approved. Current status: {application.status}."
            )

        # Create VolunteerEntity
        new_volunteer = VolunteerEntity(
            first_name=application.first_name,
            last_name=application.last_name,
            email=application.email,
            public_alias=application.public_alias,
            external_handle="N/A",  # Default or derive as needed
            status="active",  # Default status for new volunteers
            incentive_points=0,  # Starting points
        )

        created_volunteer = self.volsRepo.createVolunteer(new_volunteer)
        return VolunteerResponseDto.model_validate(created_volunteer)

    def createVolunteerApplication(self, app_dto: VolunteerApplicationCreateDto) -> VolunteerApplicationResponseDto:
        # Create VolunteerApplicationEntity from DTO
        new_application = VolunteerApplicationEntity(
            first_name=app_dto.first_name,
            last_name=app_dto.last_name,
            motivation=app_dto.motivation,
            public_alias=app_dto.public_alias,
            email=app_dto.email,
            status="pending"  # Default status for new applications
        )
        created_application = self.appRepo.createVolunteerApplication(new_application)
        return VolunteerApplicationResponseDto.model_validate(created_application)

    def approveVolunteerApplication(self, application_id: uuid.UUID, admin_id: uuid.UUID | None = None) -> VolunteerApplicationResponseDto:
        application = self.appRepo.getVolunteerApplicationById(application_id)

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Volunteer application with id {application_id} not found."
            )

        if application.status == "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Volunteer application {application_id} is already approved."
            )
        if application.status == "rejected":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Volunteer application {application_id} has been rejected and cannot be approved."
            )

        approved_application = self.appRepo.approveVolunteerApplication(application_id, admin_id)
        return VolunteerApplicationResponseDto.model_validate(approved_application)
