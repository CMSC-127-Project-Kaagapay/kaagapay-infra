from sqlalchemy.orm import Session
from db import get_db
from repositories.notificationRepository import NotificationRepository
import sys
import os

# Add the lambdas directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def run_notification_fanout_worker():
    db: Session = next(get_db())
    try:
        notification_repo = NotificationRepository(db)
        unsent_notifications = notification_repo.getUnsentNotifications()

        if not unsent_notifications:
            print("No unsent notifications found.")
            return

        print(f"Found {len(unsent_notifications)} unsent notifications.")

        for notification in unsent_notifications:
            # TODO: Implement actual fanout mechanism here
            # This is where you would integrate with email services, push notification services, etc.
            print(
                f"Fanning out notification {notification.id}: Type='{notification.recipient_type}', Recipient='{notification.recipient_id}', Message='{notification.message}'"
            )

            # Mark as sent
            notification_repo.markNotificationAsSent(notification.id)
            print(f"Notification {notification.id} marked as sent.")

        db.commit()
    except Exception as e:
        print(f"Error in notification fanout worker: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    run_notification_fanout_worker()
