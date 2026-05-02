from sqlalchemy.orm import Session
from models.entities.volunteerApplications import VolunteerApplicationEntity
import uuid


class VolunteerApplicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def getVolunteerApplicationById(self, application_id: uuid.UUID):
        return (
            self.db.query(VolunteerApplicationEntity)
            .filter(VolunteerApplicationEntity.application_id == application_id)
            .first()
        )

    def getAllVolunteerApplications(self):
        return (
            self.db.query(VolunteerApplicationEntity).all()
        )


    def createVolunteerApplication(self, application: VolunteerApplicationEntity):
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application

    def approveVolunteerApplication(self, application_id: uuid.UUID, admin_id: uuid.UUID | None = None):
        application = self.getVolunteerApplicationById(application_id)
        if application:
            application.status = "approved"
            # If we add reviewed_by to VolunteerApplicationEntity, we'd set it here
            # application.reviewed_by = admin_id
            self.db.commit()
            self.db.refresh(application)
        return application

    def rejectVolunteerApplication(self, application_id: uuid.UUID, admin_id: uuid.UUID | None = None):
        application = self.getVolunteerApplicationById(application_id)
        if application:
            application.status = "rejected"
            # If we add reviewed_by to VolunteerApplicationEntity, we'd set it here
            # application.reviewed_by = admin_id
            self.db.commit()
            self.db.refresh(application)
        return application

