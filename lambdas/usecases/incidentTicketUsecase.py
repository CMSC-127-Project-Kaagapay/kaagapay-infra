from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models.entities.incidentTickets import IncidentTicketEntity
from models.entities.notifications import NotificationEntity
from repositories.incidentTicketRepository import IncidentTicketRepository
from repositories.volunteersRepository import VolunteerRepository
from repositories.adminRepository import AdminRepository
from repositories.notificationRepository import NotificationRepository
from models.dto.incidentTicketDto import IncidentTicketCreateDto, IncidentTicketResponseDto
import uuid
from datetime import datetime, timedelta
from typing import List


class IncidentTicketUsecase:
    def __init__(self,
                 incident_repo: IncidentTicketRepository,
                 volunteer_repo: VolunteerRepository,
                 admin_repo: AdminRepository,
                 notification_repo: NotificationRepository
                ):
        self.incident_repo = incident_repo
        self.volunteer_repo = volunteer_repo
        self.admin_repo = admin_repo
        self.notification_repo = notification_repo

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

        new_incident = IncidentTicketEntity(
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
                ticket_id=created_incident.case_id,
                recipient_type="Volunteer",
                recipient_id=str(assigned_volunteer_id),
                message=f"New incident assigned to you: {created_incident.case_id}"
            )
        elif incident_dto.routing_type == "random":
            # Notify all available volunteers
            all_volunteers = self.volunteer_repo.getAllVolunteers()
            for vol in all_volunteers:
                self._create_notification(
                    ticket_id=created_incident.case_id,
                    recipient_type="Volunteer",
                    recipient_id=str(vol.id),
                    message=f"New incident available in 'Open Cases': {created_incident.case_id}"
                )

        # Secondary notifications to allied offices (all admins)
        all_admins = self.admin_repo.getAllAdmins()
        for admin in all_admins:
            self._create_notification(
                ticket_id=created_incident.case_id,
                recipient_type="Admin",
                recipient_id=str(admin.id),
                message=f"New incident report: {created_incident.case_id} for {created_incident.locality}"
            )
        # -----------------------------------------------------------------

        return IncidentTicketResponseDto.model_validate(created_incident)

    def claimIncidentTicket(self, case_id: uuid.UUID, volunteer_id: uuid.UUID) -> IncidentTicketResponseDto:
        # Start a transaction to ensure atomicity and prevent race conditions
        with self.incident_repo.db.begin():
            incident = self.incident_repo.getIncidentTicketById(case_id)

            if not incident:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Incident ticket with ID {case_id} not found."
                )

            if incident.status != "pending" or incident.assigned_volunteer_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Incident ticket {case_id} is already {incident.status} or assigned."
                )

            # Assign the volunteer and update status
            incident.assigned_volunteer_id = volunteer_id
            incident.status = "claimed"
            updated_incident = self.incident_repo.updateIncidentTicket(incident) # Update and commit within the transaction

            # Notify the volunteer who claimed the ticket
            self._create_notification(
                ticket_id=updated_incident.case_id,
                recipient_type="Volunteer",
                recipient_id=str(volunteer_id),
                message=f"You have successfully claimed incident ticket: {updated_incident.case_id}"
            )
            # Optionally notify admins that a ticket has been claimed
            all_admins = self.admin_repo.getAllAdmins()
            for admin in all_admins:
                self._create_notification(
                    ticket_id=updated_incident.case_id,
                    recipient_type="Admin",
                    recipient_id=str(admin.id),
                    message=f"Incident ticket {updated_incident.case_id} has been claimed by Volunteer {volunteer_id}"
                )

            return IncidentTicketResponseDto.model_validate(updated_incident)

    def getIncidentTicket(self, case_id: uuid.UUID) -> IncidentTicketResponseDto:
        incident = self.incident_repo.getIncidentTicketById(case_id)
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident ticket with ID {case_id} not found."
            )
        return IncidentTicketResponseDto.model_validate(incident)

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