from sqlalchemy.orm import Session
from models.entities.incidentTickets import IncidentTicketEntity
import uuid
from datetime import datetime

class IncidentTicketRepository:
    def __init__(self, db: Session):
        self.db = db

    def createIncidentTicket(self, incident_ticket: IncidentTicketEntity) -> IncidentTicketEntity:
        self.db.add(incident_ticket)
        self.db.commit()
        self.db.refresh(incident_ticket)
        return incident_ticket

    def getIncidentTicketById(self, id: uuid.UUID) -> IncidentTicketEntity | None:
        return self.db.query(IncidentTicketEntity).filter(IncidentTicketEntity.id == id).first()

    def getIncidentTicketByPublicId(self, public_case_id: str) -> IncidentTicketEntity | None:
        return self.db.query(IncidentTicketEntity).filter(IncidentTicketEntity.public_case_id == public_case_id).first()

    def updateIncidentTicket(self, incident_ticket: IncidentTicketEntity) -> IncidentTicketEntity:
        self.db.commit()
        self.db.refresh(incident_ticket)
        return incident_ticket

    def getTimedOutPendingTickets(self) -> list[IncidentTicketEntity]:
        # Query for tickets that are 'requested' (specific assignment), assigned, and past their expiration time
        return (
            self.db.query(IncidentTicketEntity)
            .filter(
                IncidentTicketEntity.status == "requested",
                IncidentTicketEntity.assigned_volunteer_id.isnot(None),
                IncidentTicketEntity.expires_at < datetime.now()
            )
            .all()
        )

    def getPendingTicketsNoVolunteers(self) -> list[IncidentTicketEntity]:
        # Query for tickets that are pending and have no assigned volunteer
        return (
            self.db.query(IncidentTicketEntity)
            .filter(
                IncidentTicketEntity.status == "pending",
                IncidentTicketEntity.assigned_volunteer_id.is_(None)
            )
            .all()
        )

    def getRequestedTicketsForVolunteer(self, volunteer_id: uuid.UUID) -> list[IncidentTicketEntity]:
        # Query for tickets specifically requested to a certain volunteer
        return (
            self.db.query(IncidentTicketEntity)
            .filter(
                IncidentTicketEntity.status == "requested",
                IncidentTicketEntity.assigned_volunteer_id == volunteer_id
            )
            .all()
        )

    def getAllIncidentTickets(self) -> list[IncidentTicketEntity]:
        # Get all tickets for admin dashboard
        return (
            self.db.query(IncidentTicketEntity)
            .order_by(IncidentTicketEntity.created_at.desc())
            .all()
        )
