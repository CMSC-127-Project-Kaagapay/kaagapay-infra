from sqlalchemy.orm import Session
from models.entities.notifications import NotificationEntity
import uuid
from typing import List

class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def createNotification(self, notification: NotificationEntity) -> NotificationEntity:
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def getUnsentNotifications(self) -> list[NotificationEntity]:
        return self.db.query(NotificationEntity).filter(NotificationEntity.status == "unread").all()

    def markNotificationAsSent(self, notification_id: uuid.UUID):
        notification = self.db.query(NotificationEntity).filter(NotificationEntity.id == notification_id).first()
        if notification:
            notification.status = "sent"
            self.db.commit()

    def getNotificationsByRecipient(self, recipient_id: str, recipient_type: str = None) -> List[NotificationEntity]:
        """Get all notifications for a specific recipient, optionally filtered by type."""
        query = self.db.query(NotificationEntity).filter(NotificationEntity.recipient_id == recipient_id)
        if recipient_type:
            query = query.filter(NotificationEntity.recipient_type == recipient_type)
        return query.order_by(NotificationEntity.sent_at.desc()).all()
