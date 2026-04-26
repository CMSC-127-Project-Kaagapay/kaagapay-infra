from sqlalchemy.orm import Session
from models.entities.incidentTickets import IncidentTicketEntity
import uuid

class IncidentTicketRepository:
    def __init__(self, db: Session):
        self.db = db

    def createIncidentTicket(self, incident_ticket: IncidentTicketEntity) -> IncidentTicketEntity:
        self.db.add(incident_ticket)
        self.db.commit()
        self.db.refresh(incident_ticket)
        return incident_ticket

    def getIncidentTicketById(self, case_id: uuid.UUID) -> IncidentTicketEntity | None:
        return self.db.query(IncidentTicketEntity).filter(IncidentTicketEntity.case_id == case_id).first()

    def updateIncidentTicket(self, incident_ticket: IncidentTicketEntity) -> IncidentTicketEntity:
        self.db.commit()
        self.db.refresh(incident_ticket)
        return incident_ticket

    def getTimedOutPendingTickets(self) -> list[IncidentTicketEntity]:
        # Query for tickets that are pending, assigned, and past their expiration time
        return (
            self.db.query(IncidentTicketEntity)
            .filter(
                IncidentTicketEntity.status == "pending",
                IncidentTicketEntity.assigned_volunteer_id.isnot(None),
                IncidentTicketEntity.expires_at < datetime.now()
            )
            .all()
        )
