from sqlalchemy.orm import Session
from models.entities.incidentTickets import IncidentTicketEntity
import uuid
from datetime import date, datetime, time, timedelta, timezone

class IncidentTicketRepository:
    def __init__(self, db: Session):
        self.db = db

    def createIncidentTicket(self, incident_ticket: IncidentTicketEntity) -> IncidentTicketEntity:
        self.db.add(incident_ticket)
        self.db.commit()
        self.db.refresh(incident_ticket)
        return incident_ticket

    def _live(self):
        # Every normal read starts here so soft-deleted tickets never leak into lists, counts or lookups.
        return self.db.query(IncidentTicketEntity).filter(IncidentTicketEntity.deleted_at.is_(None))

    def getIncidentTicketById(self, id: uuid.UUID) -> IncidentTicketEntity | None:
        return self._live().filter(IncidentTicketEntity.id == id).first()

    def getIncidentTicketByPublicId(self, public_case_id: str, include_deleted: bool = False) -> IncidentTicketEntity | None:
        query = self.db.query(IncidentTicketEntity) if include_deleted else self._live()
        return query.filter(IncidentTicketEntity.public_case_id == public_case_id).first()

    def getTicketsByStatus(self, ticket_status: str) -> list[IncidentTicketEntity]:
        return (
            self._live()
            .filter(IncidentTicketEntity.status == ticket_status)
            .order_by(IncidentTicketEntity.created_at.desc(), IncidentTicketEntity.id.desc())
            .all()
        )

    def _filtered(self, ticket_status: str, volunteer_id: uuid.UUID | None, date_from: date | None, date_to: date | None):
        # One builder for rows and counts, so the total always equals what the list can page through.
        query = self._live().filter(IncidentTicketEntity.status == ticket_status)
        if volunteer_id is not None:
            query = query.filter(IncidentTicketEntity.assigned_volunteer_id == volunteer_id)
        if date_from is not None:
            query = query.filter(
                IncidentTicketEntity.created_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
            )
        if date_to is not None:
            # date_to is inclusive: everything before the start of the next day.
            query = query.filter(
                IncidentTicketEntity.created_at < datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc)
            )
        return query

    def getTicketsPage(
        self,
        ticket_status: str,
        volunteer_id: uuid.UUID | None,
        date_from: date | None,
        date_to: date | None,
        page: int,
        page_size: int,
    ) -> tuple[list[IncidentTicketEntity], int]:
        query = self._filtered(ticket_status, volunteer_id, date_from, date_to)
        total = query.count()
        items = (
            query
            .order_by(IncidentTicketEntity.created_at.desc(), IncidentTicketEntity.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def getDeletedTickets(self) -> list[IncidentTicketEntity]:
        return (
            self.db.query(IncidentTicketEntity)
            .filter(IncidentTicketEntity.deleted_at.isnot(None))
            .order_by(IncidentTicketEntity.deleted_at.desc(), IncidentTicketEntity.id.desc())
            .all()
        )

    def softDeleteTicket(self, ticket: IncidentTicketEntity, admin_id: uuid.UUID, reason: str | None) -> IncidentTicketEntity:
        ticket.deleted_at = datetime.now(timezone.utc)
        ticket.deleted_by = admin_id
        ticket.deleted_reason = reason
        return self.updateIncidentTicket(ticket)

    def restoreTicket(self, ticket: IncidentTicketEntity) -> IncidentTicketEntity:
        ticket.deleted_at = None
        ticket.deleted_by = None
        ticket.deleted_reason = None
        return self.updateIncidentTicket(ticket)

    def updateIncidentTicket(self, incident_ticket: IncidentTicketEntity) -> IncidentTicketEntity:
        self.db.commit()
        self.db.refresh(incident_ticket)
        return incident_ticket

    def getTimedOutPendingTickets(self) -> list[IncidentTicketEntity]:
        # Query for tickets that are 'requested' (specific assignment), assigned, and past their expiration time
        return (
            self._live()
            .filter(
                IncidentTicketEntity.status == "requested",
                IncidentTicketEntity.assigned_volunteer_id.isnot(None),
                IncidentTicketEntity.expires_at < datetime.now(timezone.utc)
            )
            .all()
        )

    def getPendingTicketsNoVolunteers(self) -> list[IncidentTicketEntity]:
        # Query for tickets that are pending and have no assigned volunteer
        return (
            self._live()
            .filter(
                IncidentTicketEntity.status == "pending",
                IncidentTicketEntity.assigned_volunteer_id.is_(None)
            )
            .all()
        )

    def getRequestedTicketsForVolunteer(self, volunteer_id: uuid.UUID) -> list[IncidentTicketEntity]:
        # Query for tickets specifically requested to a certain volunteer
        return (
            self._live()
            .filter(
                IncidentTicketEntity.status == "requested",
                IncidentTicketEntity.assigned_volunteer_id == volunteer_id
            )
            .all()
        )

    def getAllIncidentTickets(self) -> list[IncidentTicketEntity]:
        # Get all tickets for admin dashboard
        return (
            self._live()
            .order_by(IncidentTicketEntity.created_at.desc(), IncidentTicketEntity.id.desc())
            .all()
        )
