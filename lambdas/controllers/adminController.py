from datetime import date
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
import uuid
from typing import List

from db import get_db
from utils.errors import internal_error
from models.dto.adminDto import AdminCreateDto, AdminMeDto, AdminResponseDto, NotificationResponseDto, AdminStatsDto
from models.dto.incidentTicketDto import IncidentTicketResponseDto, DeletedTicketResponseDto, TicketDeleteDto, TicketPageResponseDto
from models.dto.volunteerDto import VolunteerResponseDto
from controllers.incidentTicketController import get_incident_ticket_usecase
from usecases.incidentTicketUsecase import IncidentTicketUsecase
from models.entities.admins import AdminEntity
from repositories.adminRepository import AdminRepository
from repositories.incidentTicketRepository import IncidentTicketRepository
from repositories.notificationRepository import NotificationRepository
from repositories.volunteersRepository import VolunteerRepository
from utils.auth import get_current_admin, get_current_user_id

router = APIRouter()


# --- Admin Routes ---

@router.get("/admin/me", response_model=AdminMeDto)
async def get_me(
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin)
):
    """Returns the signed-in admin (403 for anyone who is not an admin)."""
    return AdminMeDto.model_validate(AdminRepository(db).getAdminById(admin_id))


@router.get("/admin/stats", response_model=AdminStatsDto)
async def get_admin_stats(
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin)
):
    """
    Admin dashboard: Returns real aggregate statistics and incident trends.
    """
    try:
        return AdminRepository(db).getAdminStats()
    except Exception as e:
        raise internal_error(e)


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
        raise internal_error(e)


@router.get("/admin/tickets/deleted", response_model=List[DeletedTicketResponseDto])
async def get_deleted_tickets(
    incident_usecase: IncidentTicketUsecase = Depends(get_incident_ticket_usecase),
    admin_id: uuid.UUID = Depends(get_current_admin)
):
    """
    Admin dashboard: Retrieves soft-deleted tickets, newest deletion first.
    """
    return incident_usecase.getDeletedTickets()


@router.delete("/admin/tickets/{public_case_id}", response_model=DeletedTicketResponseDto)
async def delete_ticket(
    public_case_id: str,
    body: TicketDeleteDto = TicketDeleteDto(),
    incident_usecase: IncidentTicketUsecase = Depends(get_incident_ticket_usecase),
    admin_id: uuid.UUID = Depends(get_current_admin)
):
    """
    Admin dashboard: Soft-deletes a ticket. It disappears from all lists and can be restored.
    """
    return incident_usecase.deleteTicket(public_case_id, admin_id, body.reason)


@router.post("/admin/tickets/{public_case_id}/restore", response_model=IncidentTicketResponseDto)
async def restore_ticket(
    public_case_id: str,
    incident_usecase: IncidentTicketUsecase = Depends(get_incident_ticket_usecase),
    admin_id: uuid.UUID = Depends(get_current_admin)
):
    """
    Admin dashboard: Restores a soft-deleted ticket.
    """
    return incident_usecase.restoreTicket(public_case_id)


TicketStatusParam = Literal["pending", "requested", "claimed", "in_progress", "resolved", "closed"]


@router.get("/admin/tickets/{ticket_status}", response_model=TicketPageResponseDto)
async def get_tickets_by_status(
    ticket_status: TicketStatusParam,
    volunteer_id: Optional[uuid.UUID] = Query(None, description="Only tickets assigned to this volunteer"),
    date_from: Optional[date] = Query(None, description="Created on or after this date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Created on or before this date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin)
):
    """
    Admin dashboard: one page of incident tickets for a status, newest first.
    Optional filters: volunteer_id, date_from, date_to (inclusive).
    """
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from must be on or before date_to.",
        )
    incident_repo = IncidentTicketRepository(db)
    tickets, total = incident_repo.getTicketsPage(ticket_status, volunteer_id, date_from, date_to, page, page_size)
    return TicketPageResponseDto(
        items=[IncidentTicketResponseDto.model_validate(t) for t in tickets],
        total=total,
        page=page,
        page_size=page_size,
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
        raise internal_error(e)


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
        raise internal_error(e)


@router.post("/admin", response_model=AdminResponseDto, status_code=status.HTTP_201_CREATED)
async def create_admin(
    admin_dto: AdminCreateDto,
    caller_id: uuid.UUID = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Makes the Supabase account `id` an admin. Only an existing admin may call this (403 otherwise).
    The very first admin is added directly in the database.
    """
    try:
        admin_repo = AdminRepository(db)
        
        # Check if already an admin
        if admin_repo.getAdminById(admin_dto.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already an admin."
            )
            
        new_admin = AdminEntity(
            id=admin_dto.id,
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
        raise internal_error(e)


def _update_volunteer_status(db: Session, volunteer_id: uuid.UUID, new_status: str) -> VolunteerResponseDto:
    """Update a volunteer's status (e.g. 'revoked' or 'active') and return the DTO."""
    volunteer_repo = VolunteerRepository(db)
    volunteer = volunteer_repo.getVolunteerById(volunteer_id)
    if not volunteer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Volunteer not found")
    volunteer.status = new_status
    updated = volunteer_repo.updateVolunteer(volunteer)
    return VolunteerResponseDto.model_validate(updated)


@router.get("/admin/volunteers", response_model=List[VolunteerResponseDto])
async def get_admin_volunteers(
    include_revoked: bool = Query(True),
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin),
):
    """Admin dashboard: Retrieves volunteers, optionally including revoked ones."""
    try:
        volunteers = VolunteerRepository(db).getAllVolunteers(include_revoked=include_revoked)
        return [VolunteerResponseDto.model_validate(v) for v in volunteers]
    except Exception as e:
        raise internal_error(e)


@router.patch("/admin/volunteers/{volunteer_id}/revoke", response_model=VolunteerResponseDto)
async def revoke_volunteer(
    volunteer_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin),
):
    """Admin dashboard: Soft-revokes a volunteer so they are hidden from public and report lists."""
    return _update_volunteer_status(db, volunteer_id, "revoked")


@router.patch("/admin/volunteers/{volunteer_id}/restore", response_model=VolunteerResponseDto)
async def restore_volunteer(
    volunteer_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin),
):
    """Admin dashboard: Restores a revoked volunteer back to active status."""
    return _update_volunteer_status(db, volunteer_id, "active")

