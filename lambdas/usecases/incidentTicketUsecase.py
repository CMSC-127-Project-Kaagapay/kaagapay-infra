from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models.entities.incidentTickets import IncidentTicketEntity
from models.entities.notifications import NotificationEntity
from models.entities.ticketStatusLogs import TicketStatusLogEntity
from repositories.incidentTicketRepository import IncidentTicketRepository
from repositories.volunteersRepository import VolunteerRepository
from repositories.adminRepository import AdminRepository
from repositories.notificationRepository import NotificationRepository
from repositories.ticketStatusLogRepository import TicketStatusLogRepository
from models.dto.incidentTicketDto import IncidentTicketCreateDto, IncidentTicketResponseDto, TicketStatusLogResponseDto
import uuid
from datetime import datetime, timedelta
from typing import List
import random
import string

# Valid status transitions
VALID_TRANSITIONS = {
    "pending": ["claimed"],
    "claimed": ["in_progress"],
    "in_progress": ["resolved"],
    "resolved": ["closed"],
    "closed": [],
}


class IncidentTicketUsecase:
    def __init__(self,
                 incident_repo: IncidentTicketRepository,
                 volunteer_repo: VolunteerRepository,
                 admin_repo: AdminRepository,
                 notification_repo: NotificationRepository,
                 status_log_repo: TicketStatusLogRepository = None
                ):
        self.incident_repo = incident_repo
        self.volunteer_repo = volunteer_repo
        self.admin_repo = admin_repo
        self.notification_repo = notification_repo
        self.status_log_repo = status_log_repo

    def createIncidentReport(self, incident_dto: IncidentTicketCreateDto) -> IncidentTicketResponseDto:
        # Determine status and assigned volunteer based on routing type
        ticket_status = "pending"
        assigned_volunteer_id = None

        if incident_dto.routing_type == "specific":
            if not incident_dto.selected_volunteer_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_NOT_FOUND,
                    detail="Specific routing requires a selected_volunteer_id."
                )
            # Verify volunteer exists
            volunteer = self.volunteer_repo.getVolunteerById(incident_dto.selected_volunteer_id)
            if not volunteer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Volunteer with ID {incident_dto.selected_volunteer_id} not found."
                )
            assigned_volunteer_id = incident_dto.selected_volunteer_id
            # Status remains 'pending' until claimed

        elif incident_dto.routing_type == "random":
            # Status remains 'pending' for open cases pool
            pass
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid routing_type. Must be 'specific' or 'random'."
            )

        # Calculate expiration time (15 minutes from now)
        created_at = datetime.now()
        expires_at = created_at + timedelta(minutes=15)

        # Generate Public Case ID (e.g. KGPY-9A3F-88B2)
        random_part_1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        random_part_2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        public_case_id = f"KGPY-{random_part_1}-{random_part_2}"

        new_incident = IncidentTicketEntity(
            public_case_id=public_case_id,
            demographic=incident_dto.demographic,
            locality=incident_dto.locality,
            involved_party=incident_dto.involved_party,
            routing_type=incident_dto.routing_type,
            status=ticket_status,
            assigned_volunteer_id=assigned_volunteer_id,
            created_at=created_at,
            expires_at=expires_at
        )

        created_incident = self.incident_repo.createIncidentTicket(new_incident)

        # --- Notification Creation Logic ---
        if incident_dto.routing_type == "specific":
            # Notify specific volunteer
            self._create_notification(
                ticket_id=created_incident.id,
                recipient_type="Volunteer",
                recipient_id=str(assigned_volunteer_id),
                message=f"New incident assigned to you: {created_incident.public_case_id}"
            )
        elif incident_dto.routing_type == "random":
            # Notify all available volunteers
            all_volunteers = self.volunteer_repo.getAllVolunteers()
            for vol in all_volunteers:
                self._create_notification(
                    ticket_id=created_incident.id,
                    recipient_type="Volunteer",
                    recipient_id=str(vol.id),
                    message=f"New incident available in 'Open Cases': {created_incident.public_case_id}"
                )

        # Secondary notifications to allied offices (all admins)
        all_admins = self.admin_repo.getAllAdmins()
        for admin in all_admins:
            self._create_notification(
                ticket_id=created_incident.id,
                recipient_type="Admin",
                recipient_id=str(admin.id),
                message=f"New incident report: {created_incident.public_case_id} for {created_incident.locality}"
            )
        # -----------------------------------------------------------------

        return IncidentTicketResponseDto.model_validate(created_incident)

    def claimIncidentTicket(self, public_case_id: str, volunteer_id: uuid.UUID) -> IncidentTicketResponseDto:
        # Start a transaction to ensure atomicity and prevent race conditions
        with self.incident_repo.db.begin():
            incident = self.incident_repo.getIncidentTicketByPublicId(public_case_id)

            if not incident:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Incident ticket with ID {public_case_id} not found."
                )

            if incident.status != "pending" or incident.assigned_volunteer_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Incident ticket {public_case_id} is already {incident.status} or assigned."
                )

            # Assign the volunteer and update status
            incident.assigned_volunteer_id = volunteer_id
            incident.status = "claimed"
            updated_incident = self.incident_repo.updateIncidentTicket(incident) # Update and commit within the transaction

            # Notify the volunteer who claimed the ticket
            self._create_notification(
                ticket_id=updated_incident.id,
                recipient_type="Volunteer",
                recipient_id=str(volunteer_id),
                message=f"You have successfully claimed incident ticket: {updated_incident.public_case_id}"
            )
            # Optionally notify admins that a ticket has been claimed
            all_admins = self.admin_repo.getAllAdmins()
            for admin in all_admins:
                self._create_notification(
                    ticket_id=updated_incident.id,
                    recipient_type="Admin",
                    recipient_id=str(admin.id),
                    message=f"Incident ticket {updated_incident.public_case_id} has been claimed by Volunteer {volunteer_id}"
                )

            return IncidentTicketResponseDto.model_validate(updated_incident)

    def getIncidentTicket(self, public_case_id: str) -> IncidentTicketResponseDto:
        incident = self.incident_repo.getIncidentTicketByPublicId(public_case_id)
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident ticket with ID {public_case_id} not found."
            )
        return IncidentTicketResponseDto.model_validate(incident)

    def getAllPendingTicketsNoVolunteers(self) -> List[IncidentTicketResponseDto]:
        incidents = self.incident_repo.getPendingTicketsNoVolunteers()
        return [IncidentTicketResponseDto.model_validate(incident) for incident in incidents]

    def getRequestedTicketsForVolunteer(self, volunteer_id: uuid.UUID) -> List[IncidentTicketResponseDto]:
        incidents = self.incident_repo.getRequestedTicketsForVolunteer(volunteer_id)
        return [IncidentTicketResponseDto.model_validate(incident) for incident in incidents]

    def updateTicketStatus(self, public_case_id: str, new_status: str, volunteer_id: uuid.UUID) -> IncidentTicketResponseDto:
        incident = self.incident_repo.getIncidentTicketByPublicId(public_case_id)

        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident ticket with ID {public_case_id} not found."
            )

        # Validate the volunteer is the one assigned to this ticket
        if incident.assigned_volunteer_id != volunteer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not the assigned volunteer for this ticket."
            )

        # Validate the status transition
        current_status = incident.status
        allowed = VALID_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition from '{current_status}' to '{new_status}'. Allowed: {allowed}"
            )

        # Log the status change
        if self.status_log_repo:
            log = TicketStatusLogEntity(
                ticket_id=incident.id,
                volunteer_id=volunteer_id,
                from_status=current_status,
                to_status=new_status,
            )
            self.status_log_repo.createStatusLog(log)

        # Update the ticket status
        incident.status = new_status
        updated_incident = self.incident_repo.updateIncidentTicket(incident)

        # Notify admins about the status change
        all_admins = self.admin_repo.getAllAdmins()
        for admin in all_admins:
            self._create_notification(
                ticket_id=updated_incident.id,
                recipient_type="Admin",
                recipient_id=str(admin.id),
                message=f"Ticket {public_case_id} status changed: {current_status} → {new_status}"
            )

        return IncidentTicketResponseDto.model_validate(updated_incident)

    def getTicketStatusLogs(self, public_case_id: str) -> List[TicketStatusLogResponseDto]:
        incident = self.incident_repo.getIncidentTicketByPublicId(public_case_id)
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident ticket with ID {public_case_id} not found."
            )
        if not self.status_log_repo:
            return []
        logs = self.status_log_repo.getLogsByTicketId(incident.id)
        return [TicketStatusLogResponseDto.model_validate(log) for log in logs]

    # Helper method for creating notifications
    def _create_notification(self, ticket_id: uuid.UUID, recipient_type: str, recipient_id: str, message: str):
        new_notification = NotificationEntity(
            message=message,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            ticket_id=ticket_id,
            status="unread" # or "pending_fanout"
        )
        self.notification_repo.createNotification(new_notification)