from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
from typing import List

from db import get_db
from models.dto.adminDto import AdminCreateDto, AdminResponseDto, NotificationResponseDto
from models.dto.incidentTicketDto import IncidentTicketResponseDto
from models.entities.admins import AdminEntity
from repositories.adminRepository import AdminRepository
from repositories.incidentTicketRepository import IncidentTicketRepository
from repositories.notificationRepository import NotificationRepository
from repositories.volunteersRepository import VolunteerRepository
from utils.auth import get_current_admin, get_current_user_id

router = APIRouter()


# --- Admin Routes ---

@router.get("/admin/tickets", response_model=List[IncidentTicketResponseDto])
async def get_all_tickets(
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin)
):
    """
    Admin dashboard: Retrieves all incident tickets regardless of status.
    """
    try:
        incident_repo = IncidentTicketRepository(db)
        tickets = incident_repo.getAllIncidentTickets()
        return [IncidentTicketResponseDto.model_validate(t) for t in tickets]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )


@router.get("/admin/tickets/{ticket_status}", response_model=List[IncidentTicketResponseDto])
async def get_tickets_by_status(
    ticket_status: str,
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin)
):
    """
    Admin dashboard: Retrieves all incident tickets filtered by status.
    Valid statuses: pending, claimed, in_progress, resolved, closed
    """
    from models.entities.incidentTickets import IncidentTicketEntity

    try:
        incident_repo = IncidentTicketRepository(db)
        tickets = (
            db.query(IncidentTicketEntity)
            .filter(IncidentTicketEntity.status == ticket_status)
            .order_by(IncidentTicketEntity.created_at.desc())
            .all()
        )
        return [IncidentTicketResponseDto.model_validate(t) for t in tickets]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )



@router.get("/admin/notifications/{admin_id}", response_model=List[NotificationResponseDto])
async def get_admin_notifications(
    admin_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin_id: uuid.UUID = Depends(get_current_admin)
):
    """
    Retrieves all notifications for a specific admin.
    """
    try:
        admin_repo = AdminRepository(db)
        admin = admin_repo.getAdminById(admin_id)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Admin with ID {admin_id} not found.",
            )

        notification_repo = NotificationRepository(db)
        notifications = notification_repo.getNotificationsByRecipient(
            recipient_id=str(admin_id),
            recipient_type="Admin",
        )
        return [NotificationResponseDto.model_validate(n) for n in notifications]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )


@router.get("/admin/admins", response_model=List[AdminResponseDto])
async def get_all_admins(
    db: Session = Depends(get_db),
    current_admin_id: uuid.UUID = Depends(get_current_admin)
):
    """
    Retrieves all admins.
    """
    try:
        admin_repo = AdminRepository(db)
        admins = admin_repo.getAllAdmins()
        return [AdminResponseDto.model_validate(a) for a in admins]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )


@router.post("/admin", response_model=AdminResponseDto, status_code=status.HTTP_201_CREATED)
async def create_admin(
    admin_dto: AdminCreateDto,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Registers the authenticated user as an admin.
    Use this to create your initial admin account.
    """
    try:
        admin_repo = AdminRepository(db)
        
        # Check if already an admin
        if admin_repo.getAdminById(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already an admin."
            )
            
        new_admin = AdminEntity(
            id=user_id,
            first_name=admin_dto.first_name,
            last_name=admin_dto.last_name,
            email=admin_dto.email,
            username=admin_dto.username,
            role=admin_dto.role or "admin",
            office_id=admin_dto.office_id
        )
        
        return admin_repo.createAdmin(new_admin)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )

