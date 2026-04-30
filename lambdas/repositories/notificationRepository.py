from sqlalchemy.orm import Session
from models.entities.notifications import NotificationEntity
import uuid

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

