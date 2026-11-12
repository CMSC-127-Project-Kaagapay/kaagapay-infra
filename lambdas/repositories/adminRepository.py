from collections import defaultdict
from datetime import datetime, timezone
import uuid
from typing import List
from sqlalchemy import func
from sqlalchemy.orm import Session
from models.entities.admins import AdminEntity
from models.entities.incidentTickets import IncidentTicketEntity
from models.entities.volunteerApplications import VolunteerApplicationEntity
from models.entities.volunteers import VolunteerEntity

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

class AdminRepository:
    def __init__(self, db: Session):
        self.db = db

    def getAllAdmins(self) -> List[AdminEntity]:
        return self.db.query(AdminEntity).all()

    def getAdminById(self, admin_id: uuid.UUID) -> AdminEntity | None:
        return self.db.query(AdminEntity).filter(AdminEntity.id == admin_id).first()

    def createAdmin(self, admin: AdminEntity) -> AdminEntity:
        self.db.add(admin)
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def getAdminStats(self) -> dict:
        # Group ticket counts by status for non-deleted tickets
        status_rows = (
            self.db.query(IncidentTicketEntity.status, func.count(IncidentTicketEntity.id))
            .filter(IncidentTicketEntity.deleted_at.is_(None))
            .group_by(IncidentTicketEntity.status)
            .all()
        )
        status_counts = dict(status_rows)

        pending_reports = status_counts.get("pending", 0) + status_counts.get("requested", 0)
        claimed_reports = status_counts.get("claimed", 0)
        in_progress_reports = status_counts.get("in_progress", 0)
        active_reports = pending_reports + claimed_reports + in_progress_reports

        resolved_tickets = status_counts.get("resolved", 0) + status_counts.get("closed", 0)
        total_tickets = sum(status_counts.values())
        resolution_rate = round((resolved_tickets / total_tickets * 100), 1) if total_tickets > 0 else 0.0

        # Volunteer applications count in 'pending' status
        pending_applications = (
            self.db.query(func.count(VolunteerApplicationEntity.application_id))
            .filter(VolunteerApplicationEntity.status == "pending")
            .scalar() or 0
        )

        # Active volunteers count
        active_volunteers = (
            self.db.query(func.count(VolunteerEntity.id))
            .filter(VolunteerEntity.status == "active")
            .scalar() or 0
        )

        # Incident trends: Monthly (last 6 months) and Quarterly (last 4 quarters)
        now = datetime.now(timezone.utc)
        curr_y, curr_m = now.year, now.month
        curr_q = (curr_m - 1) // 3 + 1

        all_created_records = (
            self.db.query(IncidentTicketEntity.created_at)
            .filter(IncidentTicketEntity.deleted_at.is_(None))
            .all()
        )

        month_counts = defaultdict(int)
        quarter_counts = defaultdict(int)

        for (created_at,) in all_created_records:
            if created_at is None:
                continue
            if isinstance(created_at, str):
                try:
                    dt = datetime.fromisoformat(created_at.replace(" ", "T"))
                except Exception:
                    continue
            else:
                dt = created_at
            month_counts[(dt.year, dt.month)] += 1
            q = (dt.month - 1) // 3 + 1
            quarter_counts[(dt.year, q)] += 1

        monthly_list = []
        for offset in range(5, -1, -1):
            total_m = curr_y * 12 + (curr_m - 1) - offset
            y = total_m // 12
            m = total_m % 12 + 1
            monthly_list.append({
                "label": MONTH_NAMES[m - 1],
                "year": y,
                "month": m,
                "count": month_counts[(y, m)],
            })

        quarterly_list = []
        for offset in range(3, -1, -1):
            total_q = curr_y * 4 + (curr_q - 1) - offset
            qy = total_q // 4
            qq = total_q % 4 + 1
            quarterly_list.append({
                "label": f"Q{qq} {qy}",
                "year": qy,
                "quarter": qq,
                "count": quarter_counts[(qy, qq)],
            })

        return {
            "active_reports": active_reports,
            "pending_reports": pending_reports,
            "claimed_reports": claimed_reports,
            "in_progress_reports": in_progress_reports,
            "total_tickets": total_tickets,
            "resolved_tickets": resolved_tickets,
            "resolution_rate": resolution_rate,
            "pending_applications": pending_applications,
            "active_volunteers": active_volunteers,
            "incident_trends": {
                "monthly": monthly_list,
                "quarterly": quarterly_list,
            },
        }
