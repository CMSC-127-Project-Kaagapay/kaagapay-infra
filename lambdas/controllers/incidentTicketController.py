from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from db import get_db
from models.dto.incidentTicketDto import (
    IncidentTicketCreateDto,
    IncidentTicketResponseDto,
)
from repositories.incidentTicketRepository import IncidentTicketRepository
from repositories.volunteersRepository import VolunteerRepository
from repositories.adminRepository import AdminRepository
from repositories.notificationRepository import NotificationRepository
from usecases.incidentTicketUsecase import IncidentTicketUsecase

router = APIRouter()


# Dependency to get IncidentTicketUsecase
def get_incident_ticket_usecase(
    db: Session = Depends(get_db),
) -> IncidentTicketUsecase:
    incident_repo = IncidentTicketRepository(db)
    volunteer_repo = VolunteerRepository(db)
    admin_repo = AdminRepository(db)
    notification_repo = NotificationRepository(db)
    return IncidentTicketUsecase(
        incident_repo, volunteer_repo, admin_repo, notification_repo
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


@router.post("/incidents/{public_case_id}/claim", response_model=IncidentTicketResponseDto)
async def claim_incident_ticket(
    public_case_id: str,
    # TODO: Implement actual authentication to get the volunteer_id
    # For now, we'll assume a volunteer_id is passed or hardcoded for testing
    volunteer_id: uuid.UUID,  # Placeholder for the ID of the volunteer claiming the ticket
    incident_usecase: IncidentTicketUsecase = Depends(get_incident_ticket_usecase),
):
    """
    Allows a volunteer to claim an open incident ticket.
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
