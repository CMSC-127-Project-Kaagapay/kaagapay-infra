from sqlalchemy.orm import Session
from models.entities.alliedOffices import AlliedOfficeEntity
from typing import List
import uuid

class AlliedOfficeRepository:
    def __init__(self, db: Session):
        self.db = db

    def getAllOffices(self) -> List[AlliedOfficeEntity]:
        return self.db.query(AlliedOfficeEntity).all()

    def getOfficeById(self, office_id: uuid.UUID) -> AlliedOfficeEntity | None:
        return self.db.query(AlliedOfficeEntity).filter(AlliedOfficeEntity.id == office_id).first()
