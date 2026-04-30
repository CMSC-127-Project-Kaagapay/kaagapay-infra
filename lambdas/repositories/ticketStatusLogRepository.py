from sqlalchemy.orm import Session
from models.entities.ticketStatusLogs import TicketStatusLogEntity
import uuid
from typing import List


class TicketStatusLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def createStatusLog(self, log: TicketStatusLogEntity) -> TicketStatusLogEntity:
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def getLogsByTicketId(self, ticket_id: uuid.UUID) -> List[TicketStatusLogEntity]:
        return (
            self.db.query(TicketStatusLogEntity)
            .filter(TicketStatusLogEntity.ticket_id == ticket_id)
            .all()
        )
