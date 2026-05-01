from sqlalchemy.orm import Session
from models.entities.admins import AdminEntity
from typing import List
import uuid

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