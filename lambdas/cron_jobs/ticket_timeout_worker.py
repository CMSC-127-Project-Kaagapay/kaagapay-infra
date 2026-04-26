from sqlalchemy.orm import Session
from datetime import datetime
from db import get_db_session
from repositories.incidentTicketRepository import IncidentTicketRepository
from models.entities.incidentTickets import IncidentTicketEntity
import sys
import os

# Add the lambdas directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_ticket_timeout_worker():
    db: Session = next(get_db_session()) # Use next() to get the session object
    try:
        incident_repo = IncidentTicketRepository(db)
        timed_out_tickets = incident_repo.getTimedOutPendingTickets()

        if not timed_out_tickets:
            print("No timed-out tickets found.")
            return

        print(f"Found {len(timed_out_tickets)} timed-out tickets.")

        for ticket in timed_out_tickets:
            # Revert the ticket to the open cases pool
            ticket.assigned_volunteer_id = None
            ticket.routing_type = "random"
            ticket.status = "pending" # Back to pending for open cases pool
            incident_repo.updateIncidentTicket(ticket)
            print(f"Ticket {ticket.case_id} timed out and moved to open cases pool.")

            # TODO: Create a notification for admins about this timeout
            # This would involve:
            # 1. Initializing NotificationRepository and AdminRepository
            # 2. Iterating through admins and creating a NotificationEntity for each
            #    e.g., notification_repo.createNotification(...)

        db.commit() # Commit all changes
    except Exception as e:
        print(f"Error in ticket timeout worker: {e}")
        db.rollback() # Rollback in case of error
    finally:
        db.close()

if __name__ == "__main__":
    run_ticket_timeout_worker()
