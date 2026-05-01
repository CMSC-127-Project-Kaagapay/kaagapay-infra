from fastapi import HTTPException, status
from models.entities.volunteers import VolunteerEntity
from models.entities.volunteerApplications import VolunteerApplicationEntity
from repositories.volunteersRepository import VolunteerRepository
from repositories.volunteerApplicationRepository import VolunteerApplicationRepository
from models.dto.volunteerDto import VolunteerResponseDto, VolunteerApplicationCreateDto, VolunteerApplicationResponseDto, VolunteerUpdateDto
import uuid
from typing import List, Dict
from supabase import create_client, Client
import os


class VolunteersUsecase:
    def __init__(self, volsRepo: VolunteerRepository, appRepo: VolunteerApplicationRepository):
        self.volsRepo = volsRepo
        self.appRepo = appRepo
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not supabase_url or not supabase_key:
            raise RuntimeError("Supabase environment variables not set for VolunteersUsecase.")
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'profiles')


    def _map_volunteer_to_dto(self, volunteer: VolunteerEntity) -> VolunteerResponseDto:
        dto = VolunteerResponseDto.model_validate(volunteer)
        if volunteer.profile_image_key:
            # Generate a public URL for Supabase Storage
            # get_public_url is fast and synchronous (just string concatenation)
            dto.profile_image_url = self.supabase.storage.from_(self.S3_BUCKET_NAME).get_public_url(volunteer.profile_image_key)
        return dto

    def getAllVolunteers(self) -> List[VolunteerResponseDto]:
        try:
            volunteers_entities = self.volsRepo.getAllVolunteers()
            return [self._map_volunteer_to_dto(v) for v in volunteers_entities]
        except Exception as e:
            raise e

    def getVolunteerById(self, volunteer_id: uuid.UUID) -> VolunteerResponseDto:
        volunteer = self.volsRepo.getVolunteerById(volunteer_id)
        if not volunteer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Volunteer not found")
        return self._map_volunteer_to_dto(volunteer)

    def getProfileImageUploadUrl(self) -> Dict[str, str]:
        # Generate a random key for the image
        key = f"profiles/{uuid.uuid4()}.jpg" # Can be customized based on requirements
        
        # Use Supabase Storage to create a signed upload URL.
        # create_signed_upload_url typically has a default expiry (e.g., 60 seconds).
        response = self.supabase.storage.from_(self.S3_BUCKET_NAME).create_signed_upload_url(key)
        
        if not response or not response.get('signedUrl'): # Ensure 'signedUrl' exists in the response
            print(f"Supabase create_signed_upload_url response: {response}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not generate upload URL from Supabase.")
        
        # Supabase's create_signed_upload_url returns a dictionary with 'signedUrl'
        return {"upload_url": response['signedUrl'], "key": key}

    def updateVolunteer(self, volunteer_id: uuid.UUID, update_dto: VolunteerUpdateDto) -> VolunteerResponseDto:
        volunteer = self.volsRepo.getVolunteerById(volunteer_id)
        if not volunteer:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Volunteer not found")
        
        update_data = update_dto.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "profile_image_key": # Update profile_image_key in entity
                setattr(volunteer, "profile_image_key", value)
            else:
                setattr(volunteer, key, value)

        updated_volunteer = self.volsRepo.updateVolunteer(volunteer)
        return self._map_volunteer_to_dto(updated_volunteer)


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

        # Initialize Supabase Admin Client
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase environment variables not set."
            )

        supabase: Client = create_client(supabase_url, supabase_key)

        try:
            # Create the user in Supabase Auth
            auth_response = supabase.auth.admin.invite_user_by_email(application.email)
            
            # The newly created Supabase Auth user ID
            supabase_user_id = auth_response.user.id 

            # Create the Volunteer Entity using the Supabase ID
            new_volunteer = VolunteerEntity(
                id=uuid.UUID(supabase_user_id), # Bind the DB record to the Auth record
                first_name=application.first_name,
                last_name=application.last_name,
                email=application.email,
                public_alias=application.public_alias,
                external_handle="N/A", 
                status="active", 
                incentive_points=0, 
            )
            self.volsRepo.createVolunteer(new_volunteer)

            # Mark the application as approved
            approved_application = self.appRepo.approveVolunteerApplication(application_id, admin_id)
            return VolunteerApplicationResponseDto.model_validate(approved_application)
            
        except Exception as e:
            print(f"Failed to approve volunteer and create account: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create account and approve application: {e}"
            )

