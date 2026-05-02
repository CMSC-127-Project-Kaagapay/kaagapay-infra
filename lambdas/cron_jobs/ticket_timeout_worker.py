from sqlalchemy.orm import Session
from datetime import datetime
from db import get_db
from repositories.incidentTicketRepository import IncidentTicketRepository
from repositories.adminRepository import AdminRepository
from repositories.notificationRepository import NotificationRepository
from models.entities.incidentTickets import IncidentTicketEntity
from models.entities.notifications import NotificationEntity
import sys
import os

# Add the lambdas directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_ticket_timeout_worker():
    db: Session = next(get_db()) # Use next() to get the session object
    try:
        incident_repo = IncidentTicketRepository(db)
        admin_repo = AdminRepository(db)
        notification_repo = NotificationRepository(db)

        timed_out_tickets = incident_repo.getTimedOutPendingTickets()

        if not timed_out_tickets:
            print("No timed-out tickets found.")
            return

        print(f"Found {len(timed_out_tickets)} timed-out tickets.")

        # Fetch all admins once for notification fanout
        all_admins = admin_repo.getAllAdmins()

        for ticket in timed_out_tickets:
            expired_volunteer_id = ticket.assigned_volunteer_id

            # Revert the ticket to the open cases pool
            ticket.assigned_volunteer_id = None
            ticket.routing_type = "random"
            ticket.status = "pending" # Back to pending for open cases pool
            incident_repo.updateIncidentTicket(ticket)
            print(f"Ticket {ticket.public_case_id} timed out and moved to open cases pool.")

            # Notify all admins about the timeout
            for admin in all_admins:
                notification = NotificationEntity(
                    message=f"Ticket {ticket.public_case_id} timed out. Volunteer {expired_volunteer_id} did not respond within 15 minutes. Moved to open cases pool.",
                    recipient_type="Admin",
                    recipient_id=str(admin.id),
                    ticket_id=ticket.id,
                    status="unread"
                )
                db.add(notification)

        db.commit() # Commit all changes
    except Exception as e:
        print(f"Error in ticket timeout worker: {e}")
        db.rollback() # Rollback in case of error
    finally:
        db.close()

if __name__ == "__main__":
    run_ticket_timeout_worker()
