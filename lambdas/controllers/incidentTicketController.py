from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
from typing import List

from db import get_db
from models.dto.incidentTicketDto import (
    IncidentTicketCreateDto,
    IncidentTicketResponseDto,
    TicketStatusUpdateDto,
    TicketStatusLogResponseDto,
)
from models.dto.adminDto import NotificationResponseDto
from repositories.incidentTicketRepository import IncidentTicketRepository
from repositories.volunteersRepository import VolunteerRepository
from repositories.adminRepository import AdminRepository
from repositories.notificationRepository import NotificationRepository
from repositories.ticketStatusLogRepository import TicketStatusLogRepository
from usecases.incidentTicketUsecase import IncidentTicketUsecase
from utils.auth import get_current_user_id

router = APIRouter()


# Dependency to get IncidentTicketUsecase
def get_incident_ticket_usecase(
    db: Session = Depends(get_db),
) -> IncidentTicketUsecase:
    incident_repo = IncidentTicketRepository(db)
    volunteer_repo = VolunteerRepository(db)
    admin_repo = AdminRepository(db)
    notification_repo = NotificationRepository(db)
    status_log_repo = TicketStatusLogRepository(db)
    return IncidentTicketUsecase(
        incident_repo, volunteer_repo, admin_repo, notification_repo, status_log_repo
    )


@router.post(
    "/incidents",
    response_model=IncidentTicketResponseDto,
    status_code=status.HTTP_201_CREATED,
)
async def create_incident_report(
    incident_dto: IncidentTicketCreateDto,
    incident_usecase: IncidentTicketUsecase = Depends(get_incident_ticket_usecase),
):
    """
    Allows a victim to create a new incident report.
    """
    try:
        new_incident = incident_usecase.createIncidentReport(incident_dto)
        return new_incident
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )


@router.get("/incidents/pending", response_model=List[IncidentTicketResponseDto])
async def get_all_pending_tickets(
    user_id: uuid.UUID = Depends(get_current_user_id),
    incident_usecase: IncidentTicketUsecase = Depends(get_incident_ticket_usecase),
):
    """
    Retrieves all pending tickets with no assigned volunteers (open cases pool).
    """
    try:
        return incident_usecase.getAllPendingTicketsNoVolunteers()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )


@router.get("/incidents/requested", response_model=List[IncidentTicketResponseDto])
async def get_requested_tickets_for_volunteer(
    volunteer_id: uuid.UUID = Depends(get_current_user_id),
    incident_usecase: IncidentTicketUsecase = Depends(get_incident_ticket_usecase),
):
    """
    Retrieves all pending tickets specifically requested to the authenticated volunteer.
    """
    try:
        return incident_usecase.getRequestedTicketsForVolunteer(volunteer_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )


@router.post("/incidents/{public_case_id}/claim", response_model=IncidentTicketResponseDto)
async def claim_incident_ticket(
    public_case_id: str,
    volunteer_id: uuid.UUID = Depends(get_current_user_id),
    incident_usecase: IncidentTicketUsecase = Depends(get_incident_ticket_usecase),
):
    """
    Allows a volunteer to claim an open incident ticket using their access token.
    """
    try:
        claimed_ticket = incident_usecase.claimIncidentTicket(public_case_id, volunteer_id)
        return claimed_ticket
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )


@router.get("/incidents/{public_case_id}", response_model=IncidentTicketResponseDto)
async def get_incident_ticket(
    public_case_id: str,
    incident_usecase: IncidentTicketUsecase = Depends(get_incident_ticket_usecase),
):
    """
    Allows a victim to retrieve the status of their incident ticket.
    """
    try:
        incident = incident_usecase.getIncidentTicket(public_case_id)
        return incident
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )


@router.patch("/incidents/{public_case_id}/status", response_model=IncidentTicketResponseDto)
async def update_ticket_status(
    public_case_id: str,
    status_update: TicketStatusUpdateDto,
    volunteer_id: uuid.UUID = Depends(get_current_user_id),
    incident_usecase: IncidentTicketUsecase = Depends(get_incident_ticket_usecase),
):
    """
    Allows the assigned volunteer to update a ticket's status.
    Valid transitions: claimed → in_progress → resolved → closed
    """
    try:
        updated = incident_usecase.updateTicketStatus(
            public_case_id, status_update.status, volunteer_id
        )
        return updated
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )


@router.get("/incidents/{public_case_id}/logs", response_model=List[TicketStatusLogResponseDto])
async def get_ticket_status_logs(
    public_case_id: str,
    incident_usecase: IncidentTicketUsecase = Depends(get_incident_ticket_usecase),
):
    """
    Retrieves the full status change history for a ticket.
    """
    try:
        return incident_usecase.getTicketStatusLogs(public_case_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )


@router.get("/volunteers/notifications", response_model=List[NotificationResponseDto])
async def get_volunteer_notifications(
    volunteer_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Retrieves all notifications for the authenticated volunteer.
    Requires a valid Supabase access token.
    """
    try:
        notification_repo = NotificationRepository(db)
        notifications = notification_repo.getNotificationsByRecipient(
            recipient_id=str(volunteer_id),
            recipient_type="Volunteer",
        )
        return [NotificationResponseDto.model_validate(n) for n in notifications]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )
