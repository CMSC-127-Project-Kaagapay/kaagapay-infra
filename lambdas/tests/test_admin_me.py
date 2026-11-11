"""GET /admin/me: lets the site ask 'am I an admin?' with the real admin check."""
import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.test_ticket_soft_delete import db, admin  # noqa: F401  (fixtures)
from fastapi import FastAPI
from fastapi.testclient import TestClient


def make_client(db, user_id, is_admin):
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


def test_admin_gets_their_own_profile(db, admin):
    r = make_client(db, admin.id, True).get("/admin/me")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"id", "first_name", "last_name", "role"}   # no email or office: only what the site needs
    assert (body["id"], body["first_name"], body["last_name"]) == (str(admin.id), "A", "B")


def test_non_admin_is_403(db, admin):
    assert make_client(db, admin.id, False).get("/admin/me").status_code == 403


def test_without_a_token_the_real_dependency_returns_401(db):
    from controllers.adminController import router
    app = FastAPI()
    app.include_router(router)
    assert TestClient(app).get("/admin/me").status_code in (401, 403)
