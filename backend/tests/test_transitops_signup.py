from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

import backend.models
from backend.api.v1.endpoints.auth_api import SignupRequest
from backend.api.v1.endpoints.auth_api import GoogleAuthRequest
from backend.api.v1.endpoints.auth_api import google_auth_callback
from backend.api.v1.endpoints.auth_api import signup
from backend.core.base_model import Environment
from backend.core.database import Base
from backend.core.database import SessionLocal
from backend.core.database import engine


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client_request():
    return SimpleNamespace(headers={}, client=SimpleNamespace(host="127.0.0.1"))


def seed_required_records(env):
    env["timezone"].create({
        "name": "UTC",
        "display_name": "UTC",
        "offset": "+00:00",
    })
    for role_name in ("fleet_manager", "driver", "safety_officer", "financial_analyst"):
        env["role"].create({
            "name": role_name,
            "display_name": role_name.replace("_", " ").title(),
            "description": role_name.replace("_", " ").title(),
        })


def test_signup_driver_creates_linked_driver(db, client_request):
    env = Environment(db)
    seed_required_records(env)

    response = signup(SignupRequest(
        email="driver@example.com",
        password="Password1!",
        full_name="Transit Driver",
        role="driver",
        contact_number="5550100",
        license_number="LIC-SIGNUP-1",
        license_category="HMV",
        license_expiry_date=date(2030, 1, 1),
    ), client_request, db)

    user = env["user"].search([("email", "=", "driver@example.com")], limit=1)
    driver = env["driver"].search([("user_id", "=", user.id)], limit=1)

    assert response["success"] is True
    assert response["user"]["role"]["name"] == "driver"
    assert response["driver"]["id"] == driver.id
    assert driver.status == "available"
    assert driver.license_number == "LIC-SIGNUP-1"


def test_signup_rejects_admin_role(db, client_request):
    env = Environment(db)
    seed_required_records(env)

    with pytest.raises(ValidationError):
        SignupRequest(
            email="admin-self@example.com",
            password="Password1!",
            full_name="Self Admin",
            role="admin",
        )


def test_google_signup_creates_selected_transitops_role(db, client_request, monkeypatch):
    env = Environment(db)
    seed_required_records(env)

    from backend.api.v1.endpoints import auth_api

    monkeypatch.setattr(auth_api.google_oauth, "is_configured", lambda: True)
    monkeypatch.setattr(auth_api.google_oauth, "exchange_code_for_token", lambda code: {"access_token": "google-token"})
    monkeypatch.setattr(auth_api.google_oauth, "get_user_info", lambda token: {
        "email": "google@example.com",
        "name": "Google User",
    })

    response = google_auth_callback(GoogleAuthRequest(
        code="auth-code",
        state="state",
        role="financial_analyst",
    ), client_request, db)

    user = env["user"].search([("email", "=", "google@example.com")], limit=1)

    assert response["success"] is True
    assert response["user"]["role"]["name"] == "financial_analyst"
    assert user.role.name == "financial_analyst"
    assert user.last_login_at is not None


def test_google_signup_rejects_new_user_without_selected_role(db, client_request, monkeypatch):
    env = Environment(db)
    seed_required_records(env)

    from backend.api.v1.endpoints import auth_api

    monkeypatch.setattr(auth_api.google_oauth, "is_configured", lambda: True)
    monkeypatch.setattr(auth_api.google_oauth, "exchange_code_for_token", lambda code: {"access_token": "google-token"})
    monkeypatch.setattr(auth_api.google_oauth, "get_user_info", lambda token: {
        "email": "new-google@example.com",
        "name": "New Google User",
    })

    with pytest.raises(HTTPException) as exc_info:
        google_auth_callback(GoogleAuthRequest(
            code="auth-code",
            state="state",
        ), client_request, db)

    assert exc_info.value.status_code == 400
    assert "Choose a TransitOps role" in exc_info.value.detail
