"""POST /admin: only an existing admin may make someone an admin.

These tests keep the REAL admin check (get_current_admin reads the admins table); only the token and the
database are replaced, so a signed-in non-admin must really be refused.
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.test_ticket_soft_delete import db, admin  # noqa: F401  (fixtures)
from fastapi import FastAPI
from fastapi.testclient import TestClient

from models.entities.admins import AdminEntity


def client_as(db, user_id):
    from controllers.adminController import router
    from db import get_db
    from utils.auth import get_current_user_id

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    return TestClient(app)


def body(account_id, email="new@b.c"):
    return {"id": str(account_id), "first_name": "N", "last_name": "M", "email": email}


def test_a_signed_in_non_admin_cannot_make_themselves_an_admin(db, admin):
    stranger = uuid.uuid4()
    r = client_as(db, stranger).post("/admin", json=body(stranger))
    assert r.status_code == 403
    assert db.query(AdminEntity).filter(AdminEntity.id == stranger).first() is None


def test_a_signed_in_non_admin_cannot_make_someone_else_an_admin(db, admin):
    stranger, friend = uuid.uuid4(), uuid.uuid4()
    assert client_as(db, stranger).post("/admin", json=body(friend)).status_code == 403
    assert db.query(AdminEntity).filter(AdminEntity.id == friend).first() is None


def test_an_admin_can_make_another_account_an_admin(db, admin):
    new_id = uuid.uuid4()
    r = client_as(db, admin.id).post("/admin", json=body(new_id))
    assert r.status_code == 201
    assert r.json()["id"] == str(new_id)
    assert db.query(AdminEntity).filter(AdminEntity.id == new_id).first() is not None


def test_making_an_existing_admin_again_is_a_400(db, admin):
    r = client_as(db, admin.id).post("/admin", json=body(admin.id, email="other@b.c"))
    assert r.status_code == 400


def test_without_a_token_the_real_dependencies_refuse(db):
    from controllers.adminController import router
    app = FastAPI()
    app.include_router(router)
    assert TestClient(app).post("/admin", json=body(uuid.uuid4())).status_code in (401, 403)
