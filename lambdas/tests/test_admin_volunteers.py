"""Tests for admin volunteer listing, soft-revocation, and restoration."""
import os
import sys
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.test_ticket_soft_delete import db, admin  # noqa: F401
from models.entities.volunteers import VolunteerEntity
from repositories.volunteersRepository import VolunteerRepository


def _make_client(db, user_id, is_admin):
    from controllers.adminController import router
    from db import get_db
    from utils.auth import get_current_admin

    def current_admin():
        if not is_admin:
            raise HTTPException(status_code=403, detail="Access denied: User is not an admin")
        return user_id

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_admin] = current_admin
    return TestClient(app)


def _seed_volunteer(db, alias="Responder One", status="active"):
    volunteer = VolunteerEntity(
        id=uuid.uuid4(),
        first_name="Jane",
        last_name="Doe",
        email=f"{uuid.uuid4().hex[:8]}@up.edu.ph",
        public_alias=alias,
        external_handle="@janedoe",
        status=status,
    )
    db.add(volunteer)
    db.commit()
    db.refresh(volunteer)
    return volunteer


def test_admin_can_list_revoke_and_restore_volunteers(db, admin):
    active_vol = _seed_volunteer(db, alias="Active Responder", status="active")
    revoked_vol = _seed_volunteer(db, alias="Revoked Responder", status="revoked")
    client = _make_client(db, admin.id, True)

    # Public repository query excludes revoked volunteers by default
    public_list = VolunteerRepository(db).getAllVolunteers()
    public_ids = {v.id for v in public_list}
    assert active_vol.id in public_ids
    assert revoked_vol.id not in public_ids

    # Admin endpoint returns both when include_revoked=True
    res = client.get("/admin/volunteers")
    assert res.status_code == 200
    admin_ids = {item["id"] for item in res.json()}
    assert {str(active_vol.id), str(revoked_vol.id)}.issubset(admin_ids)

    # Revoke active volunteer -> hidden from public list
    revoke_res = client.patch(f"/admin/volunteers/{active_vol.id}/revoke")
    assert revoke_res.status_code == 200
    assert revoke_res.json()["status"] == "revoked"
    assert active_vol.id not in {v.id for v in VolunteerRepository(db).getAllVolunteers()}

    # Restore revoked volunteer -> visible in public list again
    restore_res = client.patch(f"/admin/volunteers/{active_vol.id}/restore")
    assert restore_res.status_code == 200
    assert restore_res.json()["status"] == "active"
    assert active_vol.id in {v.id for v in VolunteerRepository(db).getAllVolunteers()}


def test_non_admin_cannot_access_admin_volunteers(db, admin):
    vol = _seed_volunteer(db)
    client = _make_client(db, admin.id, False)
    assert client.get("/admin/volunteers").status_code == 403
    assert client.patch(f"/admin/volunteers/{vol.id}/revoke").status_code == 403
    assert client.patch(f"/admin/volunteers/{vol.id}/restore").status_code == 403


def test_revoke_unknown_volunteer_returns_404(db, admin):
    client = _make_client(db, admin.id, True)
    assert client.patch(f"/admin/volunteers/{uuid.uuid4()}/revoke").status_code == 404
