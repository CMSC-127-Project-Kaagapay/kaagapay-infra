from sqlalchemy.orm import Session
from models.entities.volunteers import VolunteerEntity


class VolunteerRepository:
    def __init__(self, db: Session):
        self.db = db

    def getAllVolunteers(self):
        return self.db.query(VolunteerEntity).all()

    def getVolunteerById(self, volunteerId: uuid.UUID):
        return (
            self.db.query(VolunteerEntity)
            .filter(VolunteerEntity.id == volunteerId)
            .first()
        )

    def createVolunteer(self, volunteer: VolunteerEntity):
        self.db.add(volunteer)
        self.db.commit()
        self.db.refresh(volunteer)
        return volunteer
